"""Text utility functions for Desktop Utility."""
import re


def count_words(text):
    """Count characters, words, sentences, paragraphs, and lines in text."""
    if not text or not text.strip():
        return {"characters": 0, "characters_no_spaces": 0, "words": 0,
                "sentences": 0, "paragraphs": 0, "lines": 0}

    chars = len(text)
    chars_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", ""))
    words = len(text.split())
    sentences = len(re.findall(r'[.!?]+', text))
    if sentences == 0 and words > 0:
        sentences = 1
    paragraphs = len([p for p in text.split("\n\n") if p.strip()])
    lines = len(text.splitlines())

    return {
        "characters": chars,
        "characters_no_spaces": chars_no_spaces,
        "words": words,
        "sentences": sentences,
        "paragraphs": paragraphs,
        "lines": lines,
    }


def convert_case(text, mode="upper"):
    """Convert text case. Modes: upper, lower, title, sentence, alternating, inverse."""
    if mode == "upper":
        return text.upper()
    elif mode == "lower":
        return text.lower()
    elif mode == "title":
        return text.title()
    elif mode == "sentence":
        # Capitalize first letter of each sentence
        result = []
        for sentence in re.split(r'([.!?]\s*)', text):
            if sentence:
                result.append(sentence[0].upper() + sentence[1:] if sentence else sentence)
        return "".join(result)
    elif mode == "alternating":
        return "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(text))
    elif mode == "inverse":
        return text.swapcase()
    return text


def find_replace(text, find_str, replace_str, case_sensitive=True):
    """Find and replace text. Returns (new_text, count)."""
    if not find_str:
        return text, 0
    if case_sensitive:
        count = text.count(find_str)
        return text.replace(find_str, replace_str), count
    else:
        pattern = re.compile(re.escape(find_str), re.IGNORECASE)
        result = pattern.subn(replace_str, text)
        return result[0], result[1]


def generate_lorem(paragraphs=3):
    """Generate lorem ipsum placeholder text."""
    base = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        "Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius, turpis et commodo pharetra, est eros bibendum elit, nec luctus magna felis sollicitudin mauris.",
        "Praesent blandit dolor. Sed non quam. In vel mi sit amet augue congue elementum. Morbi in ipsum sit amet pede facilisis laoreet. Donec lacus nunc, viverra nec, blandit vel, egestas et, augue.",
        "Vestibulum tincidunt malesuada tellus. Ut ultrices ultrices enim. Curabitur sit amet mauris. Morbi in dui quis est pulvinar ullamcorper. Nulla facilisi. Integer lacinia sollicitudin massa.",
        "Cras metus. Sed aliquet risus a tortor. Integer id quam. Morbi mi. Quisque nisl felis, venenatis tristique, dignissim in, ultrices sit amet, augue. Proin sodales libero eget ante.",
    ]
    result = []
    for i in range(paragraphs):
        result.append(base[i % len(base)])
    return "\n\n".join(result)


def remove_extra_spaces(text):
    """Remove extra whitespace — multiple spaces, leading/trailing per line."""
    lines = text.splitlines()
    cleaned = [re.sub(r' +', ' ', line.strip()) for line in lines]
    return "\n".join(cleaned)


def count_frequency(text, top_n=10):
    """Return the most frequent words in the text."""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return sorted_freq[:top_n]
