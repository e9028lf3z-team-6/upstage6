ALTER TABLE eval_runs ADD COLUMN meta_json TEXT DEFAULT "{}";
ALTER TABLE eval_runs ADD COLUMN agent_latency_json TEXT DEFAULT "{}";
