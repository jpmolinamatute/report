DROP TABLE IF EXISTS coins;
DROP TABLE IF EXISTS wallets;
DROP TABLE IF EXISTS action_type;
CREATE TABLE action_type(name TEXT NOT NULL PRIMARY KEY);
CREATE TABLE wallets (name TEXT NOT NULL PRIMARY KEY);
CREATE TABLE coins(
    coin_token TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL
);
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
