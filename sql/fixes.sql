
-- broken migration?
update fee_entry set detect_method = 'FALLBACK' where detect_method='DetectMethod.FALLBACK';
