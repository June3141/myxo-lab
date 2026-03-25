use std::collections::HashSet;

use sha2::{Digest, Sha256};

pub struct CacheStats {
    pub total_requests: u64,
    pub cache_hits: u64,
    pub cache_misses: u64,
}

impl CacheStats {
    pub fn hit_rate(&self) -> f64 {
        if self.total_requests == 0 {
            0.0
        } else {
            self.cache_hits as f64 / self.total_requests as f64
        }
    }
}

pub struct PromptCacheManager {
    cacheable_prefixes: Vec<String>,
    seen_hashes: HashSet<[u8; 32]>,
    max_history: usize,
    cache_hits: u64,
    cache_misses: u64,
    total_requests: u64,
}

impl PromptCacheManager {
    pub fn new(cacheable_prefixes: Vec<String>) -> Self {
        Self::with_max_history(cacheable_prefixes, 10000)
    }

    pub fn with_max_history(cacheable_prefixes: Vec<String>, max_history: usize) -> Self {
        assert!(max_history > 0, "max_history must be greater than 0");
        Self {
            cacheable_prefixes,
            seen_hashes: HashSet::new(),
            max_history,
            cache_hits: 0,
            cache_misses: 0,
            total_requests: 0,
        }
    }

    pub fn is_cacheable(&self, content: &str) -> bool {
        if content.is_empty() {
            return false;
        }
        self.cacheable_prefixes
            .iter()
            .any(|prefix| content.starts_with(prefix))
    }

    pub fn track(&mut self, content: &str) {
        if !self.is_cacheable(content) {
            return;
        }

        let hash: [u8; 32] = Sha256::digest(content.as_bytes()).into();
        self.total_requests += 1;

        if self.seen_hashes.contains(&hash) {
            self.cache_hits += 1;
        } else {
            self.cache_misses += 1;
            if self.seen_hashes.len() >= self.max_history {
                self.seen_hashes.clear();
            }
            self.seen_hashes.insert(hash);
        }
    }

    pub fn stats(&self) -> CacheStats {
        CacheStats {
            total_requests: self.total_requests,
            cache_hits: self.cache_hits,
            cache_misses: self.cache_misses,
        }
    }
}

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
        cache.track("Log entry 1");
        cache.track("Log entry 2");

        let stats = cache.stats();
        assert_eq!(stats.total_requests, 3);
        assert_eq!(stats.cache_hits, 1);
        assert_eq!(stats.cache_misses, 2);
    }

    #[test]
    fn stats_hit_rate() {
        let mut cache = PromptCacheManager::new(vec!["a".into()]);
        assert_eq!(cache.stats().hit_rate(), 0.0);

        cache.track("a");
        cache.track("a");
        assert!((cache.stats().hit_rate() - 0.5).abs() < f64::EPSILON);
    }

    #[test]
    fn max_history_clears_on_overflow() {
        let mut cache = PromptCacheManager::with_max_history(vec!["".into()], 2);
        cache.track("a");
        cache.track("b");
        cache.track("c");
        cache.track("a");
        assert_eq!(cache.stats().cache_hits, 0);
    }

    #[test]
    fn track_skips_non_cacheable() {
        let mut cache = PromptCacheManager::new(vec!["Log".into()]);
        cache.track("not cacheable");
        assert_eq!(cache.stats().total_requests, 0);
    }

    #[test]
    #[should_panic(expected = "max_history must be greater than 0")]
    fn zero_max_history_panics() {
        PromptCacheManager::with_max_history(vec![], 0);
    }
}
