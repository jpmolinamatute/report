PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS inventory;
DROP TABLE IF EXISTS operation_details;
DROP TABLE IF EXISTS operation;
DROP TABLE IF EXISTS ref_prices;
DROP TABLE IF EXISTS coins;
DROP TABLE IF EXISTS operation_type;
DROP TABLE IF EXISTS wallets;

CREATE TABLE operation_type(
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE wallets (
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE coins(
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE ref_prices(
    coin TEXT NOT NULL PRIMARY KEY,
    price REAL NOT NULL DEFAULT 0.00,
    FOREIGN KEY(coin) REFERENCES coins(name)
);

CREATE TABLE operation_details(
    id TEXT NOT NULL PRIMARY KEY,
    op_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    change REAL NOT NULL,
    wallet TEXT NOT NULL DEFAULT binance,
    FOREIGN KEY(op_id) REFERENCES operation(id)
    FOREIGN KEY(coin) REFERENCES coins(name)
);

CREATE TABLE operation(
    id TEXT NOT NULL PRIMARY KEY,
    utc_date TEXT NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY(name) REFERENCES operation_type(name)
);

CREATE VIEW inventory AS
SELECT coin, ROUND(SUM(change),8) AS change
FROM operation_details
GROUP BY coin
HAVING ROUND(SUM(change),8) > 0
ORDER BY coin;

INSERT INTO operation_type(name)
VALUES
("BUY"),
("SELL"),
("FEE"),
("DEPOSIT"),
("WITHDRAW"),
("ADJUSTMENT"),
("CONVERTION"),
("INTEREST");

INSERT INTO coins(name)
VALUES
("BTC"),
("ETH"),
("BNB"),
("AXS"),
("XMR"),
("ADA"),
("XRP"),
("DOT"),
("SOL"),
("UNI"),
("USDT"),
("BUSD"),
("LTC"),
("DOGE"),
("SLP");

INSERT INTO ref_prices (coin, price)
VALUES
("BTC", 49865.86),
("ETH", 3879.57),
("BNB", 495.8),
("AXS", 88.7),
("XMR", 304.0),
("ADA", 2.860),
("XRP", 1.2554),
("DOT", 33.02),
("SOL", 140.19),
("UNI", 28.69),
("SLP", 0.1249);

INSERT INTO wallets(name)
VALUES
("binance"),
("daedalus"),
("metamask");
