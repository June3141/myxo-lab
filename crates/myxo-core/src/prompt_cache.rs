// PromptCache module - to be implemented

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn is_cacheable_matches_prefix() {
        let cache = PromptCacheManager::new(vec!["Ship's Log".into(), "Skills".into()]);
        assert!(cache.is_cacheable("Ship's Log: entry 1"));
        assert!(cache.is_cacheable("Skills: rust"));
        assert!(!cache.is_cacheable("Random text"));
    }

    #[test]
    fn empty_content_not_cacheable() {
        let cache = PromptCacheManager::new(vec!["Test".into()]);
        assert!(!cache.is_cacheable(""));
    }

    #[test]
    fn stats_track_hits_and_misses() {
        let mut cache = PromptCacheManager::new(vec!["Log".into()]);
        cache.track("Log entry 1");
        cache.track("Log entry 1"); // hit
        cache.track("Log entry 2"); // miss

        let stats = cache.stats();
        assert_eq!(stats.total_requests, 3);
        assert_eq!(stats.cache_hits, 1);
        assert_eq!(stats.cache_misses, 2);
    }

    #[test]
    fn stats_hit_rate() {
        let mut cache = PromptCacheManager::new(vec![]);
        assert_eq!(cache.stats().hit_rate(), 0.0);

        cache.track("a");
        cache.track("a");
        assert!((cache.stats().hit_rate() - 0.5).abs() < f64::EPSILON);
    }

    #[test]
    fn max_history_clears_on_overflow() {
        let mut cache = PromptCacheManager::with_max_history(vec![], 2);
        cache.track("a");
        cache.track("b");
        cache.track("c"); // should clear and add "c"
        // After clear, "a" is no longer seen
        cache.track("a"); // miss, not hit
        assert_eq!(cache.stats().cache_hits, 0);
    }
}
