-- Add logs_url column to battle_summaries for existing databases
ALTER TABLE battle_summaries ADD COLUMN logs_url TEXT;
