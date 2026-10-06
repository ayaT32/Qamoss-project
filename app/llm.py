"""
Groq LLM wrapper. The LLM is NEVER used to generate standalone answers —
only to classify the nature of a small difference between two already
RETRIEVED texts. This is the structural hallucination guard: if retrieval
finds nothing, this module is never even called (see retrieval.py).
"""
import os

from groq import Groq

SYSTEM_PROMPT = """أنت أداة تحقق تعمل ضمن قيود صارمة:

1. لا تجب إلا بالاستناد إلى النصين المرفقين لك. لا تستخدم معرفتك العامة أبدًا.
2. ميّز دائمًا بين النص الشرعي الأصلي والشرح المولَّد؛ لا تدمجهما.
3. مهمتك تصنيف الفرق بين نصين فقط، لا إصدار حكم شرعي أو فتوى.
4. أجب بكلمة أو كلمتين فقط من هذه القائمة: "تشكيل فقط" أو "ترتيب كلمات"
   أو "إبدال كلمة" أو "حذف جزء" أو "اختلاف جوهري".
5. عند الشك بين خيارين، اختر الأكثر تحفظًا (الأقرب إلى "اختلاف جوهري")."""

_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
                "and set it as an environment variable."
            )
        _client = Groq(api_key=api_key)
    return _client


def classify_difference(user_text: str, original_text: str) -> str:
    """Classify the nature of the difference between two texts that were
    already matched as similar by retrieval. Returns a short Arabic label.
    Never called when no reference text was found.
    """
    client = get_client()
    prompt = (
        f"النص الأول (كما أدخله المستخدم):\n{user_text}\n\n"
        f"النص الثاني (من المصدر الموثق):\n{original_text}\n\n"
        "صنّف طبيعة الفرق بينهما بكلمة أو كلمتين فقط من القائمة المحددة."
    )
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=20,
    )
    return resp.choices[0].message.content.strip()
