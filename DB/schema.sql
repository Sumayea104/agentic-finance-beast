-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    hashed_password TEXT,
    google_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Portfolios
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT DEFAULT 'My Portfolio',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Holdings
CREATE TABLE holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    buy_price DECIMAL(10, 2) NOT NULL,
    buy_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- PHASE 2: PORTFOLIO + TRANSACTIONS
-- ============================================

-- 1. Portfolios (already exists, but let's ensure it)
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT DEFAULT 'My Portfolio',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Holdings (current state — calculated from transactions)
CREATE TABLE IF NOT EXISTS holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    quantity DECIMAL(12, 4) NOT NULL DEFAULT 0,
    average_buy_price DECIMAL(12, 4) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(portfolio_id, symbol)  -- One row per symbol per portfolio
);

-- 3. Transactions (historical record)
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'BUY' or 'SELL'
    quantity DECIMAL(12, 4) NOT NULL,
    price DECIMAL(12, 4) NOT NULL,
    total_amount DECIMAL(12, 4) NOT NULL,  -- quantity * price
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Enable RLS
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies (Service role can do anything)
CREATE POLICY "Service role can do anything on portfolios"
    ON portfolios USING (true) WITH CHECK (true);
CREATE POLICY "Service role can do anything on holdings"
    ON holdings USING (true) WITH CHECK (true);
CREATE POLICY "Service role can do anything on transactions"
    ON transactions USING (true) WITH CHECK (true);