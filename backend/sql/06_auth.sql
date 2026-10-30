USE inventory_management;

ALTER TABLE stock_transactions
    MODIFY created_by VARCHAR(254) NOT NULL DEFAULT 'demo-user';

CREATE TABLE app_users (
    user_id       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(254) NOT NULL,
    pending_email VARCHAR(254),
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at    TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                               ON UPDATE CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_app_users PRIMARY KEY (user_id),
    CONSTRAINT uq_app_users_email UNIQUE (email),
    CONSTRAINT uq_app_users_pending_email UNIQUE (pending_email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE user_sessions (
    session_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id    BIGINT UNSIGNED NOT NULL,
    token_hash CHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_user_sessions PRIMARY KEY (session_id),
    CONSTRAINT uq_user_sessions_token UNIQUE (token_hash),
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id)
        REFERENCES app_users (user_id) ON DELETE CASCADE,
    INDEX ix_user_sessions_expiry (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE account_tokens (
    token_hash CHAR(64) NOT NULL,
    user_id    BIGINT UNSIGNED NOT NULL,
    purpose    VARCHAR(24) NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_account_tokens PRIMARY KEY (token_hash),
    CONSTRAINT fk_account_tokens_user FOREIGN KEY (user_id)
        REFERENCES app_users (user_id) ON DELETE CASCADE,
    CONSTRAINT ck_account_tokens_purpose CHECK (
        purpose IN ('verify_email', 'change_email', 'reset_password')
    ),
    INDEX ix_account_tokens_user_purpose (user_id, purpose),
    INDEX ix_account_tokens_expiry (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
