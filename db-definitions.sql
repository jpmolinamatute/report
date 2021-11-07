PRAGMA foreign_keys = ON;
PRAGMA optimize;
DROP VIEW IF EXISTS inventory;
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
    investment REAL NOT NULL,
    wallet TEXT NOT NULL,
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


CREATE VIEW inventory AS
SELECT coin, ROUND(SUM(amount),8) AS amount
FROM (
    SELECT coin, amount FROM interest
    UNION ALL
    SELECT coin, amount FROM operation_details
    UNION ALL
    SELECT coin, amount FROM operation_fees
)
GROUP BY coin
HAVING ROUND(SUM(amount),8) > 0.00
ORDER BY coin;

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
("DAEDALUS"),
("PHANTOM");


INSERT INTO operations(id, utc_date, op_type)
VALUES
("46132b54-c1ac-4ee8-87d6-b44a62595f2e", "2021-11-07 18:31:53", "DEPOSIT"),
("d07131d4-1538-4340-9095-91ceb775ca42", "2021-11-07 18:31:53", "DEPOSIT"),
("36fed547-c2e6-4754-99c1-3bc5bfb39960", "2021-11-07 18:31:53", "DEPOSIT"),
("fae64f43-d288-4992-ad00-5feeefc31bd6", "2021-11-07 18:31:53", "DEPOSIT"),
("dfe209ad-fcca-40af-a153-155c4f7d74b4", "2021-11-07 18:31:53", "DEPOSIT"),
("47555ff4-8e7f-4531-990e-45c9ff240619", "2021-11-07 18:31:53", "DEPOSIT"),
("7a20df0f-34ef-4586-a395-768ef8821544", "2021-11-07 18:31:53", "DEPOSIT"),
("02588758-edf0-4028-9554-a9b98f659e72", "2021-11-07 18:31:53", "DEPOSIT");

INSERT INTO operation_details(id, op_id, coin, amount, investment, wallet)
VALUES
("5103db44-c794-4d78-bf36-bcca1f5f8667", "46132b54-c1ac-4ee8-87d6-b44a62595f2e", "ADA", 1025.778768, 2940.00, "DAEDALUS"),
("04891350-a0fa-4521-9fba-212e0cd6d4c7", "d07131d4-1538-4340-9095-91ceb775ca42", "ETH", 0.23632031, 1465.42, "TREZOR"),
("51f882ed-a98c-49bb-9237-c5693bbe1b02", "36fed547-c2e6-4754-99c1-3bc5bfb39960", "BTC", 0.02070514, 1718.283, "TREZOR"),
("de6e149e-9933-400e-bb79-910c7c0c0491", "fae64f43-d288-4992-ad00-5feeefc31bd6", "BTC", 0.00049, 35.067, "BINANCE"),
("0aa606f9-d3d2-42c1-b5f7-734c0b6be0c2", "dfe209ad-fcca-40af-a153-155c4f7d74b4", "BNB", 0.53200331, 325.00, "BINANCE"),
("d3c4b216-7d44-4e2a-a4f7-c4b1674a9b35", "47555ff4-8e7f-4531-990e-45c9ff240619", "DOT", 9.19, 500.00, "BINANCE"),
("bf09c012-eae8-4882-b8d9-4e454205bc63", "7a20df0f-34ef-4586-a395-768ef8821544", "ATOM", 5.99, 287.93, "BINANCE"),
("6a2b8f42-6c05-4b1f-825c-1e7227cf1385", "02588758-edf0-4028-9554-a9b98f659e72", "BUSD", 1209.252769, 1262.93, "BINANCE");
