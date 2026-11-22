-- Run with a Snowflake role permitted to create objects in the selected database.
-- Change the identifiers below to match your Snowflake environment.
CREATE DATABASE IF NOT EXISTS RETAIL_PORTFOLIO;
CREATE SCHEMA IF NOT EXISTS RETAIL_PORTFOLIO.RAW;
-- The Python loader creates RAW_ORDERS when it first runs.
