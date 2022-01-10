DROP VIEW IF EXISTS portfolio;
DROP VIEW IF EXISTS actual_investment;
DROP TABLE IF EXISTS actions;
DROP TABLE IF EXISTS coins;
DROP TABLE IF EXISTS wallets;
DROP TABLE IF EXISTS action_type;
CREATE TABLE action_type(name TEXT NOT NULL PRIMARY KEY);
CREATE TABLE wallets (name TEXT NOT NULL PRIMARY KEY);
CREATE TABLE coins(
    coin_token TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE actions(
    id UUID NOT NULL PRIMARY KEY,
    utc_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    action_type TEXT NOT NULL,
    coin TEXT NOT NULL,
    action_id BYTEA NOT NULL,
    amount NUMERIC(13, 8) NOT NULL,
    investment NUMERIC(7, 2) NOT NULL DEFAULT 0.00,
    wallet TEXT NOT NULL,
    FOREIGN KEY(coin) REFERENCES coins(coin_token),
    FOREIGN KEY(wallet) REFERENCES wallets(name),
    FOREIGN KEY(action_type) REFERENCES action_type(name)
);
CREATE VIEW portfolio AS
SELECT coin,
    SUM(amount) AS amount,
    SUM(investment) AS investment,
    SUM(investment) / SUM(amount) AS min_price
FROM actions
GROUP BY coin
HAVING SUM(amount) > 0.00
ORDER BY coin;
CREATE VIEW actual_investment AS
SELECT SUM(investment)
FROM actions
WHERE action_type IN ('DEPOSIT', 'WITHDRAW');
-- ORDER BY utc_date;
INSERT INTO action_type(name)
VALUES ('ADJUSTMENT'),
    ('DEPOSIT'),
    ('WITHDRAW'),
    ('FEE'),
    ('INTEREST'),
    ('MINING'),
    ('SWAP'),
    ('TRANSFER'),
    ('LOSS'),
    ('GAIN');
INSERT INTO coins(coin_token, name)
VALUES ('ADA', 'Cardano'),
    ('ATOM', 'Cosmos'),
    ('AXS', 'Axie Infinity'),
    ('BNB', 'Binance Coin'),
    ('BTC', 'Bitcoin'),
    ('BUSD', 'Binance USD'),
    ('DOGE', 'Dogecoin'),
    ('DOT', 'Polkadot'),
    ('ETH', 'Ethereum'),
    ('LTC', 'Litecoin'),
    ('LUNA', 'Terra'),
    ('SLP', 'Smooth Love Potion'),
    ('SOL', 'Solana'),
    ('UNI', 'Uniswap'),
    ('USDT', 'Tether'),
    ('XMR', 'Monero'),
    ('XRP', 'XRP'),
    ('SHIB', 'Shiba coin'),
    ('NA', 'NA');
INSERT INTO wallets(name)
VALUES ('BINANCE'),
    ('TREZOR'),
    ('METAMASK'),
    ('YOROI'),
    ('PHANTOM');
