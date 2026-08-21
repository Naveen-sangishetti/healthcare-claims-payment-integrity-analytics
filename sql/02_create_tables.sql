USE healthcare_payment_integrity;

CREATE TABLE IF NOT EXISTS patients_raw (
    patient_id INT,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INT,
    gender VARCHAR(20),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    phone VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS providers_raw (
    provider_id INT,
    name VARCHAR(150),
    specialty VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    phone VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS claims_raw (
    claim_id INT,
    patient_id INT,
    provider_id INT,
    claim_date DATE,
    claim_amount DECIMAL(12,2),
    status VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS payments_raw (
    claim_id INT,
    patient_id INT,
    provider_id INT,
    claim_date DATE,
    claim_amount DECIMAL(12,2),
    status VARCHAR(20),
    payment_id INT,
    payment_date DATE,
    payment_amount DECIMAL(12,2)
);