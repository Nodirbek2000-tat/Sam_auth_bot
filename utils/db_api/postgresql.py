from typing import Union, List
import asyncpg
from asyncpg import Connection
from asyncpg.pool import Pool
import json
from datetime import datetime, timedelta

from data import config


class Database:
    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def create(self):
        self.pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            database=config.DB_NAME,
            port=config.DB_PORT,
        )

    async def execute(
            self,
            command,
            *args,
            fetch: bool = False,
            fetchval: bool = False,
            fetchrow: bool = False,
            execute: bool = False,
    ):
        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchrow:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
            return result

    # ==================== JADVALLARNI YARATISH ====================

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            username VARCHAR(255) NULL,
            full_name VARCHAR(255) NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_admins(self):
        sql = """
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            is_super BOOLEAN DEFAULT FALSE,
            added_by BIGINT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_channels(self):
        sql = """
        CREATE TABLE IF NOT EXISTS channels (
            id SERIAL PRIMARY KEY,
            channel_name VARCHAR(255) NOT NULL,
            channel_username VARCHAR(255) NOT NULL UNIQUE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_user_profiles(self):
        sql = """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            first_name VARCHAR(255) NOT NULL,
            last_name VARCHAR(255) NOT NULL,
            birth_date DATE NOT NULL,
            address TEXT NOT NULL,
            is_approved BOOLEAN DEFAULT FALSE,
            is_rejected BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP NULL,
            rejected_at TIMESTAMP NULL
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_initial_questions(self):
        sql = """
        CREATE TABLE IF NOT EXISTS initial_questions (
            id SERIAL PRIMARY KEY,
            question_text TEXT NOT NULL,
            field_type VARCHAR(50) DEFAULT 'text',
            options TEXT[] NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_initial_responses(self):
        sql = """
        CREATE TABLE IF NOT EXISTS initial_responses (
            id SERIAL PRIMARY KEY,
            profile_id INTEGER REFERENCES user_profiles(id) ON DELETE CASCADE,
            question_id INTEGER REFERENCES initial_questions(id) ON DELETE CASCADE,
            answer TEXT NOT NULL,
            answer_type VARCHAR(50) DEFAULT 'text',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_surveys(self):
        sql = """
        CREATE TABLE IF NOT EXISTS surveys (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            file_name VARCHAR(255) NOT NULL UNIQUE,
            is_active BOOLEAN DEFAULT FALSE,
            created_by BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_survey_fields(self):
        sql = """
        CREATE TABLE IF NOT EXISTS survey_fields (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
            field_order INTEGER NOT NULL,
            column_name VARCHAR(255) NOT NULL,
            question_text TEXT NOT NULL,
            field_type VARCHAR(50) DEFAULT 'text',
            options TEXT[] NULL
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_survey_responses(self):
        sql = """
        CREATE TABLE IF NOT EXISTS survey_responses (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL,
            response_data JSONB NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_all_tables(self):
        await self.create_table_users()
        await self.create_table_admins()
        await self.create_table_channels()
        await self.create_table_user_profiles()
        await self.create_table_initial_questions()
        await self.create_table_initial_responses()
        await self.create_table_surveys()
        await self.create_table_survey_fields()
        await self.create_table_survey_responses()

    # ==================== USERS ====================

    async def add_user(self, telegram_id: int, username: str = None, full_name: str = None):
        sql = """
        INSERT INTO users (telegram_id, username, full_name) 
        VALUES ($1, $2, $3) 
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = $2,
            full_name = $3
        RETURNING *;
        """
        return await self.execute(sql, telegram_id, username, full_name, fetchrow=True)

    async def get_user(self, telegram_id: int):
        sql = "SELECT * FROM users WHERE telegram_id = $1;"
        return await self.execute(sql, telegram_id, fetchrow=True)

    async def count_users(self):
        sql = "SELECT COUNT(*) FROM users;"
        return await self.execute(sql, fetchval=True)

    async def count_users_last_24h(self):
        sql = "SELECT COUNT(*) FROM users WHERE joined_at >= NOW() - INTERVAL '24 hours';"
        return await self.execute(sql, fetchval=True)

    async def count_users_last_week(self):
        sql = "SELECT COUNT(*) FROM users WHERE joined_at >= NOW() - INTERVAL '7 days';"
        return await self.execute(sql, fetchval=True)

    async def get_all_users(self):
        sql = "SELECT * FROM users ORDER BY joined_at DESC;"
        return await self.execute(sql, fetch=True)

    # ==================== ADMINS ====================

    async def add_admin(self, telegram_id: int, is_super: bool = False, added_by: int = None):
        sql = """
        INSERT INTO admins (telegram_id, is_super, added_by) 
        VALUES ($1, $2, $3) 
        ON CONFLICT (telegram_id) DO UPDATE SET is_super = $2
        RETURNING *;
        """
        return await self.execute(sql, telegram_id, is_super, added_by, fetchrow=True)

    async def remove_admin(self, telegram_id: int):
        sql = "DELETE FROM admins WHERE telegram_id = $1 AND is_super = FALSE RETURNING *;"
        return await self.execute(sql, telegram_id, fetchrow=True)

    async def get_admin(self, telegram_id: int):
        sql = "SELECT * FROM admins WHERE telegram_id = $1;"
        return await self.execute(sql, telegram_id, fetchrow=True)

    async def is_admin(self, telegram_id: int):
        sql = "SELECT EXISTS(SELECT 1 FROM admins WHERE telegram_id = $1);"
        return await self.execute(sql, telegram_id, fetchval=True)

    async def is_super_admin(self, telegram_id: int):
        sql = "SELECT EXISTS(SELECT 1 FROM admins WHERE telegram_id = $1 AND is_super = TRUE);"
        return await self.execute(sql, telegram_id, fetchval=True)

    async def get_all_admins(self):
        sql = "SELECT * FROM admins ORDER BY added_at DESC;"
        return await self.execute(sql, fetch=True)

    # ==================== CHANNELS ====================

    async def add_channel(self, channel_name: str, channel_username: str):
        sql = """
        INSERT INTO channels (channel_name, channel_username) 
        VALUES ($1, $2) 
        ON CONFLICT (channel_username) DO UPDATE SET channel_name = $1
        RETURNING *;
        """
        return await self.execute(sql, channel_name, channel_username, fetchrow=True)

    async def remove_channel(self, channel_id: int):
        sql = "DELETE FROM channels WHERE id = $1 RETURNING *;"
        return await self.execute(sql, channel_id, fetchrow=True)

    async def get_channel(self, channel_id: int):
        sql = "SELECT * FROM channels WHERE id = $1;"
        return await self.execute(sql, channel_id, fetchrow=True)

    async def get_all_channels(self):
        sql = "SELECT * FROM channels ORDER BY added_at DESC;"
        return await self.execute(sql, fetch=True)

    async def count_channels(self):
        sql = "SELECT COUNT(*) FROM channels;"
        return await self.execute(sql, fetchval=True)

    # ==================== USER PROFILES ====================

    async def add_user_profile(self, telegram_id: int, first_name: str, last_name: str, birth_date, address: str):
        sql = """
        INSERT INTO user_profiles (telegram_id, first_name, last_name, birth_date, address) 
        VALUES ($1, $2, $3, $4, $5) 
        ON CONFLICT (telegram_id) DO UPDATE SET
            first_name = $2,
            last_name = $3,
            birth_date = $4,
            address = $5,
            is_approved = FALSE,
            is_rejected = FALSE,
            created_at = CURRENT_TIMESTAMP
        RETURNING *;
        """
        return await self.execute(sql, telegram_id, first_name, last_name, birth_date, address, fetchrow=True)

    async def get_user_profile(self, telegram_id: int):
        sql = "SELECT * FROM user_profiles WHERE telegram_id = $1;"
        return await self.execute(sql, telegram_id, fetchrow=True)

    async def get_user_profile_by_id(self, profile_id: int):
        sql = "SELECT * FROM user_profiles WHERE id = $1;"
        return await self.execute(sql, profile_id, fetchrow=True)

    async def approve_user_profile(self, profile_id: int):
        sql = """
        UPDATE user_profiles 
        SET is_approved = TRUE, is_rejected = FALSE, approved_at = CURRENT_TIMESTAMP 
        WHERE id = $1 
        RETURNING *;
        """
        return await self.execute(sql, profile_id, fetchrow=True)

    async def reject_user_profile(self, profile_id: int):
        sql = """
        UPDATE user_profiles 
        SET is_rejected = TRUE, is_approved = FALSE, rejected_at = CURRENT_TIMESTAMP 
        WHERE id = $1 
        RETURNING *;
        """
        return await self.execute(sql, profile_id, fetchrow=True)

    async def get_pending_approvals(self):
        sql = "SELECT * FROM user_profiles WHERE is_approved = FALSE AND is_rejected = FALSE ORDER BY created_at ASC;"
        return await self.execute(sql, fetch=True)

    async def count_pending_approvals(self):
        sql = "SELECT COUNT(*) FROM user_profiles WHERE is_approved = FALSE AND is_rejected = FALSE;"
        return await self.execute(sql, fetchval=True)

    async def count_approved_users(self):
        sql = "SELECT COUNT(*) FROM user_profiles WHERE is_approved = TRUE;"
        return await self.execute(sql, fetchval=True)

    async def count_rejected_users(self):
        sql = "SELECT COUNT(*) FROM user_profiles WHERE is_rejected = TRUE;"
        return await self.execute(sql, fetchval=True)

    # ==================== INITIAL QUESTIONS ====================

    async def add_initial_question(self, question_text: str, field_type: str = 'text', options: List[str] = None,
                                   is_active: bool = True):
        sql = """
        INSERT INTO initial_questions (question_text, field_type, options, is_active) 
        VALUES ($1, $2, $3, $4) 
        RETURNING *;
        """
        return await self.execute(sql, question_text, field_type, options, is_active, fetchrow=True)

    async def get_initial_question(self, question_id: int):
        sql = "SELECT * FROM initial_questions WHERE id = $1;"
        return await self.execute(sql, question_id, fetchrow=True)

    async def get_all_initial_questions(self):
        sql = "SELECT * FROM initial_questions ORDER BY created_at ASC;"
        return await self.execute(sql, fetch=True)

    async def get_active_initial_questions(self):
        sql = "SELECT * FROM initial_questions WHERE is_active = TRUE ORDER BY created_at ASC;"
        return await self.execute(sql, fetch=True)

    async def toggle_initial_question(self, question_id: int, is_active: bool):
        sql = "UPDATE initial_questions SET is_active = $2 WHERE id = $1 RETURNING *;"
        return await self.execute(sql, question_id, is_active, fetchrow=True)

    async def delete_initial_question(self, question_id: int):
        sql = "DELETE FROM initial_questions WHERE id = $1 RETURNING *;"
        return await self.execute(sql, question_id, fetchrow=True)

    # ==================== INITIAL RESPONSES ====================

    async def add_initial_response(self, profile_id: int, question_id: int, answer, answer_type: str = 'text'):
        # Agar answer dict yoki list bo'lsa, JSON'ga aylantirish
        if isinstance(answer, (dict, list)):
            answer = json.dumps(answer)

        sql = """
        INSERT INTO initial_responses (profile_id, question_id, answer, answer_type) 
        VALUES ($1, $2, $3, $4) 
        RETURNING *;
        """
        return await self.execute(sql, profile_id, question_id, answer, answer_type, fetchrow=True)

    async def get_initial_responses(self, profile_id: int):
        sql = "SELECT * FROM initial_responses WHERE profile_id = $1 ORDER BY created_at ASC;"
        return await self.execute(sql, profile_id, fetch=True)

    # ==================== SURVEYS ====================

    async def add_survey(self, name: str, file_name: str, created_by: int):
        sql = """
        INSERT INTO surveys (name, file_name, created_by) 
        VALUES ($1, $2, $3) 
        RETURNING *;
        """
        return await self.execute(sql, name, file_name, created_by, fetchrow=True)

    async def get_survey(self, survey_id: int):
        sql = "SELECT * FROM surveys WHERE id = $1;"
        return await self.execute(sql, survey_id, fetchrow=True)

    async def get_survey_by_filename(self, file_name: str):
        sql = "SELECT * FROM surveys WHERE file_name = $1;"
        return await self.execute(sql, file_name, fetchrow=True)

    async def get_active_survey(self):
        sql = "SELECT * FROM surveys WHERE is_active = TRUE;"
        return await self.execute(sql, fetchrow=True)

    async def get_all_surveys(self):
        sql = "SELECT * FROM surveys ORDER BY created_at DESC;"
        return await self.execute(sql, fetch=True)

    async def set_survey_active(self, survey_id: int):
        await self.execute("UPDATE surveys SET is_active = FALSE;", execute=True)
        sql = "UPDATE surveys SET is_active = TRUE WHERE id = $1 RETURNING *;"
        return await self.execute(sql, survey_id, fetchrow=True)

    async def deactivate_survey(self, survey_id: int):
        sql = "UPDATE surveys SET is_active = FALSE WHERE id = $1 RETURNING *;"
        return await self.execute(sql, survey_id, fetchrow=True)

    async def delete_survey(self, survey_id: int):
        sql = "DELETE FROM surveys WHERE id = $1 RETURNING *;"
        return await self.execute(sql, survey_id, fetchrow=True)

    async def count_surveys(self):
        sql = "SELECT COUNT(*) FROM surveys;"
        return await self.execute(sql, fetchval=True)

    # ==================== SURVEY FIELDS ====================

    async def add_survey_field(
            self,
            survey_id: int,
            field_order: int,
            column_name: str,
            question_text: str,
            field_type: str = 'text',
            options: List[str] = None
    ):
        sql = """
        INSERT INTO survey_fields (survey_id, field_order, column_name, question_text, field_type, options) 
        VALUES ($1, $2, $3, $4, $5, $6) 
        RETURNING *;
        """
        return await self.execute(sql, survey_id, field_order, column_name, question_text, field_type, options,
                                  fetchrow=True)

    async def get_survey_fields(self, survey_id: int):
        sql = "SELECT * FROM survey_fields WHERE survey_id = $1 ORDER BY field_order;"
        return await self.execute(sql, survey_id, fetch=True)

    # ==================== SURVEY RESPONSES ====================

    async def add_survey_response(self, survey_id: int, user_id: int, response_data: dict):
        sql = """
        INSERT INTO survey_responses (survey_id, user_id, response_data) 
        VALUES ($1, $2, $3) 
        RETURNING *;
        """
        return await self.execute(sql, survey_id, user_id, json.dumps(response_data), fetchrow=True)

    async def get_survey_responses(self, survey_id: int):
        sql = "SELECT * FROM survey_responses WHERE survey_id = $1 ORDER BY submitted_at DESC;"
        return await self.execute(sql, survey_id, fetch=True)

    async def count_survey_responses(self, survey_id: int):
        sql = "SELECT COUNT(*) FROM survey_responses WHERE survey_id = $1;"
        return await self.execute(sql, survey_id, fetchval=True)