CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS FOR (r:Resource) REQUIRE r.uri IS UNIQUE;
CALL n10s.graphconfig.init({handleVocabUris: "IGNORE", handleMultival: "ARRAY", handleRDFTypes: "LABELS"});