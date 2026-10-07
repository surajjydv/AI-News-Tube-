import re

STOP_WORDS = {
    'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'been', 'will', 'about',
    'news', 'photo', 'image', 'video', 'live', 'today', 'latest', 'update', 'says', 'after',
    'over', 'into', 'amid', 'media', 'press', 'report', 'reports', 'online', 'post', 'daily',
    'times', 'com', 'www', 'http', 'https', 'jpg', 'png', 'jpeg', 'webp', 'html', 'upload',
    'wikimedia', 'wikipedia', 'commons', 'source', 'page', 'file', 'content', 'article',
    'year', 'years', 'month', 'first', 'last', 'also', 'more', 'when', 'what', 'which',
    'their', 'there', 'they', 'them', 'then', 'than', 'were', 'would', 'could', 'should'
}

def verify_photo_match(article_text: str, photo_meta: str, min_words: int = 5):
    if not article_text or not photo_meta:
        return False, 0, []

    def get_tokens(text: str) -> set[str]:
        raw = re.findall(r'[a-zA-Z\u0900-\u097F]{3,}', text.lower())
        return {t for t in raw if t not in STOP_WORDS}

    art_tokens = get_tokens(article_text)
    photo_tokens = get_tokens(photo_meta)

    if not art_tokens or not photo_tokens:
        return False, 0, []

    matched = set(art_tokens.intersection(photo_tokens))

    def stem(w: str) -> str:
        for suffix in ('ation', 'ment', 'ing', 'ies', 'es', 'ed', 's'):
            if w.endswith(suffix) and len(w) - len(suffix) >= 3:
                return w[:-len(suffix)]
        return w

    stem_art = {stem(w): w for w in art_tokens if len(stem(w)) >= 3}
    for pw in photo_tokens:
        p_stem = stem(pw)
        if len(p_stem) >= 3 and p_stem in stem_art:
            matched.add(stem_art[p_stem])

    matched_list = sorted(list(matched))
    return len(matched_list) >= min_words, len(matched_list), matched_list

# Test 1: Real news event photo
art = "Gyanesh Kumar: Police detain opposition leaders in Delhi demanding election commission chief's resignation - BBC"
meta1 = "https://assets.telegraphindia.com/telegraph/2026/Sep/gyanesh-kumar-detained.jpg Gyanesh Kumar history | How Gyanesh shook up Election Commission Chief and opposition leaders in Delhi"
res, count, words = verify_photo_match(art, meta1, min_words=5)
print(f"Test 1: Match={res}, Count={count}, Words={words}")
assert res is True
assert count >= 5

# Test 2: Unrelated photo
meta2 = "https://images.pexels.com/courtroom-justice-gavel-wooden.jpg Courtroom law and legal system gavel on desk"
res2, count2, words2 = verify_photo_match(art, meta2, min_words=5)
print(f"Test 2: Match={res2}, Count={count2}, Words={words2}")
assert res2 is False

# Test 3: Only 2 words match
meta3 = "https://example.com/delhi-traffic.jpg Delhi police traffic police monitoring vehicles on road"
res3, count3, words3 = verify_photo_match(art, meta3, min_words=5)
print(f"Test 3: Match={res3}, Count={count3}, Words={words3}")
assert res3 is False

print("All assertion tests passed successfully!")
