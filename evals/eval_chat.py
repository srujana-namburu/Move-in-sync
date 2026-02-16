import sys
import os
import asyncio
import warnings
warnings.filterwarnings("ignore")

# ---------------- PATH SETUP ----------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_PATH)


import importlib

def alias(name, real_name):
    try:
        module = importlib.import_module(real_name)
        sys.modules[name] = module
    except Exception:
        pass

alias("models", "backend.models")
alias("database", "backend.database")
alias("crud", "backend.crud")
alias("routes", "backend.routes")
alias("Agents", "backend.Agents")

# ---------------- IMPORT CHAT ----------------
try:
    from backend.routes.movi import chat_with_movi
except Exception as e:
    print("❌ Cannot import chat_with_movi:", e)
    exit()

# ---------------- DUMMY REQUEST ----------------
import time

class DummyRequest:
    def __init__(self, message):
        self.message = message

        # fields expected in movi.py
        self.page = "routes"
        self.context_page = "routes"
        self.session_id = f"test-session-{int(time.time())}"
        self.user_id = "test-user"

        # ⭐ new field causing error
        self.image_base64 = None

TEST_CASES = [
    "List all active routes",
    "Show available paths",
    "How many vehicles exist?"
]

async def run_eval():
    print("\n🚀 Running MoveInSync Chat Evaluations\n")

    passed = 0

    for i, q in enumerate(TEST_CASES, 1):
        try:
            req = DummyRequest(q)
            result = await chat_with_movi(req)

            print(f"\nTest {i}")
            print("Question :", q)
           # print("Response :", result)

            if result:
                print("✅ PASS")
                passed += 1
            else:
                print("❌ FAIL")

        except Exception as e:
            print(f"\n❌ Test {i} Failed:", e)

    print(f"\n📊 Score: {passed}/{len(TEST_CASES)} tests passed")

if __name__ == "__main__":
    asyncio.run(run_eval())
