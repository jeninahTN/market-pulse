import re


def parse_price_to_int(value: str):
    raw = str(value or "")
    cleaned = re.sub(r"[^0-9.]", "", raw)
    if not cleaned:
        return None
    try:
        return max(0, int(round(float(cleaned))))
    except Exception:
        return None


def number_to_english_words(number: int) -> str:
    ones = [
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
    ]
    tens = [
        "",
        "",
        "twenty",
        "thirty",
        "forty",
        "fifty",
        "sixty",
        "seventy",
        "eighty",
        "ninety",
    ]
    scales = [
        (1_000_000_000, "billion"),
        (1_000_000, "million"),
        (1_000, "thousand"),
        (1, ""),
    ]

    def chunk_to_words(n: int) -> str:
        parts = []
        if n >= 100:
            parts.append(ones[n // 100])
            parts.append("hundred")
            n %= 100
        if n >= 20:
            parts.append(tens[n // 10])
            if n % 10:
                parts.append(ones[n % 10])
        elif n > 0:
            parts.append(ones[n])
        return " ".join(parts)

    if number == 0:
        return "zero"
    if number < 0:
        return f"minus {number_to_english_words(abs(number))}"

    parts = []
    remaining = number
    for scale_value, scale_name in scales:
        if remaining >= scale_value:
            chunk = remaining // scale_value
            remaining %= scale_value
            chunk_words = chunk_to_words(chunk)
            if chunk_words:
                parts.append(chunk_words)
                if scale_name:
                    parts.append(scale_name)
    return " ".join(parts).strip()


def number_to_swahili_words(number: int) -> str:
    ones = {
        0: "sifuri",
        1: "moja",
        2: "mbili",
        3: "tatu",
        4: "nne",
        5: "tano",
        6: "sita",
        7: "saba",
        8: "nane",
        9: "tisa",
    }
    tens = {
        1: "kumi",
        2: "ishirini",
        3: "thelathini",
        4: "arobaini",
        5: "hamsini",
        6: "sitini",
        7: "sabini",
        8: "themanini",
        9: "tisini",
    }

    def under_hundred(n: int) -> str:
        if n < 10:
            return ones[n]
        if n < 20:
            if n == 10:
                return "kumi"
            return f"kumi na {ones[n - 10]}"
        ten = n // 10
        rem = n % 10
        if rem == 0:
            return tens[ten]
        return f"{tens[ten]} na {ones[rem]}"

    def under_thousand(n: int) -> str:
        if n < 100:
            return under_hundred(n)
        hundreds = n // 100
        rem = n % 100
        head = f"mia {ones[hundreds]}"
        if rem == 0:
            return head
        # Common spoken form often omits "na" after "mia", but keeping a space is fine.
        return f"{head} {under_hundred(rem)}"

    if number == 0:
        return ones[0]
    if number < 0:
        return f"hasara {number_to_swahili_words(abs(number))}"

    parts = []
    remaining = number
    scales = [
        (1_000_000_000, "bilioni"),
        (1_000_000, "milioni"),
        (1_000, "elfu"),
    ]
    for scale_value, scale_name in scales:
        if remaining >= scale_value:
            chunk = remaining // scale_value
            remaining %= scale_value
            parts.append(f"{scale_name} {number_to_swahili_words(chunk)}")

    if remaining > 0:
        parts.append(under_thousand(remaining))

    return " ".join(parts).strip()


def localized_number_words(value: str, lang: str) -> str:
    """
    Convert a numeric string like "1,800" into number words for TTS fallback.

    We intentionally avoid returning digits, because many TTS engines read
    digits in English even when a local language voice is selected.

    Currently:
    - `sw`: Swahili number words
    - everything else: English number words (safe, deterministic fallback)
    """
    lang = str(lang or "en").strip().lower()
    parsed = parse_price_to_int(value)
    if parsed is None:
        return str(value or "").strip()

    if lang == "sw":
        return number_to_swahili_words(parsed)

    return number_to_english_words(parsed)

