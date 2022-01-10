DROP VIEW IF EXISTS portfolio;
DROP VIEW IF EXISTS actual_investment;
DROP TABLE IF EXISTS actions;
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
