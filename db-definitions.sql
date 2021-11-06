PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS operation_details;
DROP TABLE IF EXISTS interest;
DROP TABLE IF EXISTS operation_fees;
DROP TABLE IF EXISTS operations;
DROP TABLE IF EXISTS coins;
DROP TABLE IF EXISTS wallets;
DROP TABLE IF EXISTS operation_type;

CREATE TABLE operation_type(
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE wallets (
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE coins(
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE operations(
    id TEXT NOT NULL PRIMARY KEY,
    utc_date TEXT NOT NULL,
    op_type TEXT NOT NULL,
    FOREIGN KEY(op_type) REFERENCES operation_type(name)
);

CREATE TABLE operation_details(
    id TEXT NOT NULL PRIMARY KEY,
    op_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    amount REAL NOT NULL,
    investment REAL DEFAULT 0.0,
    wallet TEXT NOT NULL DEFAULT BINANCE,
    FOREIGN KEY(op_id) REFERENCES operations(id),
    FOREIGN KEY(coin) REFERENCES coins(name),
    FOREIGN KEY(wallet) REFERENCES wallets(name)
);

CREATE TABLE operation_fees(
    id TEXT NOT NULL PRIMARY KEY,
    op_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    amount REAL NOT NULL,
    wallet TEXT NOT NULL DEFAULT BINANCE,
    FOREIGN KEY(op_id) REFERENCES operations(id),
    FOREIGN KEY(coin) REFERENCES coins(name),
    FOREIGN KEY(wallet) REFERENCES wallets(name)
);

CREATE TABLE interest(
    id TEXT NOT NULL PRIMARY KEY,
    op_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    amount REAL NOT NULL,
    wallet TEXT NOT NULL DEFAULT BINANCE,
    FOREIGN KEY(op_id) REFERENCES operations(id),
    FOREIGN KEY(coin) REFERENCES coins(name),
    FOREIGN KEY(wallet) REFERENCES wallets(name)
);

INSERT INTO operation_type(name)
VALUES
("ADJUSTMENT"),
("DEPOSIT"),
("FEE"),
("INTEREST"),
("SWAP"),
("TRANSFER"),
("WITHDRAW");

INSERT INTO coins(name)
VALUES
("ADA"),
("ATOM"),
("AXS"),
("BNB"),
("BTC"),
("BUSD"),
("DOGE"),
("DOT"),
("ETH"),
("LTC"),
("LUNA"),
("SLP"),
("SOL"),
("UNI"),
("USDT"),
("XMR"),
("XRP");

INSERT INTO wallets(name)
VALUES
("BINANCE"),
("TREZOR"),
("PHANTOM");
