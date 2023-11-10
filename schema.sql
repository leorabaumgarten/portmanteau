CREATE TABLE IF NOT EXISTS pronunciations (
	word	TEXT NOT NULL,
	pronunciation TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phonemes (
	phoneme	TEXT NOT NULL,
	sound_type TEXT NOT NULL
);