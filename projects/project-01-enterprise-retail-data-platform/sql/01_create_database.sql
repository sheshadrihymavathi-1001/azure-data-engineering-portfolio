/*
Project 01 - Enterprise Retail Data Platform

Purpose:
    Create the local SQL Server database used as the simulated
    enterprise OLTP source.

Environment:
    SQL Server

Note:
    This script creates the database only.
    Source tables are created by 02_create_source_tables.sql.
*/

USE master;
GO

IF DB_ID('ContosoRetailDB') IS NULL
BEGIN
    CREATE DATABASE ContosoRetailDB;
    PRINT 'Database ContosoRetailDB created.';
END
ELSE
BEGIN
    PRINT 'Database ContosoRetailDB already exists.';
END
GO

USE ContosoRetailDB;
GO

SELECT
    DB_NAME() AS database_name,
    @@SERVERNAME AS server_name;
GO
