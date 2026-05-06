from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Any
from uuid import UUID
from supabase_client import supabase
from auth import get_current_teacher

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


# ── Schemas ───────────────────────────────────────────────────────────────────

# Stored format in DB: { "q": "...", "opts": ["A","B","C","D"], "ans": 0 }
# Teacher UI sends:    { "text": "...", "options": ["A","B","C","D"], "correct_option": 0 }
# We accept both and normalise to the stored format.

class QuestionItem(BaseModel):
    # Accept both naming conventions — only one set needs to be provided
    q: Optional[str] = None
    opts: Optional[List[str]] = None
    ans: Optional[int] = None

    text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_option: Optional[int] = None

    @model_validator(mode="after")
    def normalise(self):
        # Prefer the new teacher-UI fields; fall back to the legacy DB fields
        resolved_q    = self.text    or self.q
        resolved_opts = self.options or self.opts
        resolved_ans  = self.correct_option if self.correct_option is not None else self.ans

        if not resolved_q or not resolved_q.strip():
            raise ValueError("Question text (q / text) is required.")
        if not resolved_opts or len(resolved_opts) < 2:
            raise ValueError("At least 2 options (opts / options) are required.")
        if resolved_ans is None or resolved_ans < 0 or resolved_ans >= len(resolved_opts):
            raise ValueError("ans / correct_option must be a valid option index.")

        # Normalise to the canonical stored format
        self.q    = resolved_q.strip()
        self.opts = resolved_opts
        self.ans  = resolved_ans

        # Clear the alternative fields so model_dump() stays clean
        self.text           = None
        self.options        = None
        self.correct_option = None
        return self

    def to_db(self) -> dict:
        """Return only the fields that get persisted."""
        return {"q": self.q, "opts": self.opts, "ans": self.ans}


class QuizBody(BaseModel):
    title: str
    description: Optional[str] = None
    youtube_url: Optional[str] = None
    subject: Optional[str] = None       # e.g. "Informatique"
    duration: Optional[int] = 10        # minutes
    difficulty: Optional[str] = None    # "Facile" / "Moyen" / "Difficile"
    color: Optional[str] = "bg-eval-blue"
    questions: List[QuestionItem] = []
    is_published: bool = False

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Le titre ne peut pas être vide.")
        return v.strip()


class AttemptBody(BaseModel):
    student_name: str
    score: int
    total_questions: int
    answers: list = []

    @field_validator("student_name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Le prénom est requis.")
        return v.strip()

    @field_validator("score")
    @classmethod
    def score_valid(cls, v):
        if v < 0:
            raise ValueError("Le score ne peut pas être négatif.")
        return v


# ── Helper: shape a raw Supabase row into what quiz.html expects ──────────────

def _normalise_question(raw: Any) -> dict:
    """
    Accept a question in either storage format and always return
    { q, opts, ans } so the frontend gets a consistent shape.
    Also expose the teacher-UI aliases so teacher.html works without changes.
    """
    if not isinstance(raw, dict):
        return raw
    q    = raw.get("q")    or raw.get("text", "")
    opts = raw.get("opts") or raw.get("options", [])
    ans  = raw.get("ans")
    if ans is None:
        ans = raw.get("correct_option", 0)
    return {
        # canonical storage keys
        "q":    q,
        "opts": opts,
        "ans":  ans,
        # aliases used by teacher.html question builder
        "text":           q,
        "options":        opts,
        "correct_option": ans,
    }


def fmt_quiz(row: dict) -> dict:
    # extract youtube video ID from full URL if needed
    yt_url = row.get("youtube_url") or ""
    yt_id = ""
    if "v=" in yt_url:
        yt_id = yt_url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in yt_url:
        yt_id = yt_url.split("youtu.be/")[-1].split("?")[0]
    else:
        yt_id = yt_url  # assume it's already just the ID

    questions_data = [_normalise_question(q) for q in (row.get("questions") or [])]

    return {
        "id":             row["id"],
        "name":           row.get("title", ""),
        "desc":           row.get("description", ""),
        "subject":        row.get("subject", ""),
        "duration":       row.get("duration", 10),
        "difficulty":     row.get("difficulty", "Moyen"),
        "color":          row.get("color", "bg-eval-blue"),
        "youtubeId":      yt_id,
        "youtube_url":    yt_url,
        "questions":      len(questions_data),
        "questions_data": questions_data,
        "is_published":   row.get("is_published", False),
        "teacher_id":     row.get("teacher_id", ""),
        "created_at":     row.get("created_at", ""),
    }


# ── GET /quizzes — all published quizzes (students) ──────────────────────────

@router.get("/")
def list_published_quizzes():
    res = (
        supabase.table("quizzes")
        .select("*")
        .eq("is_published", True)
        .order("created_at", desc=True)
        .execute()
    )
    return [fmt_quiz(row) for row in res.data]


# ── GET /quizzes/mine — quizzes belonging to logged-in teacher ────────────────

@router.get("/mine")
def list_my_quizzes(current_user=Depends(get_current_teacher)):
    res = (
        supabase.table("quizzes")
        .select("*")
        .eq("teacher_id", str(current_user.id))
        .order("created_at", desc=True)
        .execute()
    )
    return [fmt_quiz(row) for row in res.data]


# ── GET /quizzes/{id} — single quiz detail ────────────────────────────────────

@router.get("/{quiz_id}")
def get_quiz(quiz_id: UUID):
    res = (
        supabase.table("quizzes")
        .select("*")
        .eq("id", str(quiz_id))
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Quiz introuvable.")
    return fmt_quiz(res.data)


# ── POST /quizzes — create a quiz (teacher only) ──────────────────────────────

@router.post("/", status_code=201)
def create_quiz(body: QuizBody, current_user=Depends(get_current_teacher)):
    questions_list = [q.to_db() for q in body.questions]

    res = (
        supabase.table("quizzes")
        .insert({
            "teacher_id":   str(current_user.id),
            "title":        body.title,
            "description":  body.description,
            "youtube_url":  body.youtube_url,
            "subject":      body.subject,
            "duration":     body.duration,
            "difficulty":   body.difficulty,
            "color":        body.color,
            "questions":    questions_list,
            "is_published": body.is_published,
        })
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=500, detail="Erreur lors de la création.")
    return fmt_quiz(res.data[0])


# ── PUT /quizzes/{id} — update a quiz ────────────────────────────────────────

@router.put("/{quiz_id}")
def update_quiz(quiz_id: UUID, body: QuizBody, current_user=Depends(get_current_teacher)):
    existing = (
        supabase.table("quizzes")
        .select("teacher_id")
        .eq("id", str(quiz_id))
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Quiz introuvable.")
    if existing.data["teacher_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Ce quiz ne vous appartient pas.")

    questions_list = [q.to_db() for q in body.questions]

    res = (
        supabase.table("quizzes")
        .update({
            "title":        body.title,
            "description":  body.description,
            "youtube_url":  body.youtube_url,
            "subject":      body.subject,
            "duration":     body.duration,
            "difficulty":   body.difficulty,
            "color":        body.color,
            "questions":    questions_list,
            "is_published": body.is_published,
        })
        .eq("id", str(quiz_id))
        .execute()
    )
    return fmt_quiz(res.data[0])


# ── DELETE /quizzes/{id} ──────────────────────────────────────────────────────

@router.delete("/{quiz_id}", status_code=204)
def delete_quiz(quiz_id: UUID, current_user=Depends(get_current_teacher)):
    existing = (
        supabase.table("quizzes")
        .select("teacher_id")
        .eq("id", str(quiz_id))
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Quiz introuvable.")
    if existing.data["teacher_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Ce quiz ne vous appartient pas.")

    supabase.table("quizzes").delete().eq("id", str(quiz_id)).execute()


# ── POST /quizzes/{id}/attempt — student submits answers ─────────────────────

@router.post("/{quiz_id}/attempt", status_code=201)
def submit_attempt(quiz_id: UUID, body: AttemptBody):
    quiz = (
        supabase.table("quizzes")
        .select("id, is_published")
        .eq("id", str(quiz_id))
        .single()
        .execute()
    )
    if not quiz.data:
        raise HTTPException(status_code=404, detail="Quiz introuvable.")
    if not quiz.data["is_published"]:
        raise HTTPException(status_code=403, detail="Ce quiz n'est pas disponible.")

    res = (
        supabase.table("quiz_attempts")
        .insert({
            "quiz_id":         str(quiz_id),
            "student_name":    body.student_name,
            "score":           body.score,
            "total_questions": body.total_questions,
            "answers":         body.answers,
        })
        .execute()
    )
    return {
        "success":    True,
        "score":      body.score,
        "total":      body.total_questions,
        "percentage": round(body.score / body.total_questions * 100),
    }


# ── GET /quizzes/{id}/attempts — teacher sees results ────────────────────────

@router.get("/{quiz_id}/attempts")
def get_attempts(quiz_id: UUID, current_user=Depends(get_current_teacher)):
    quiz = (
        supabase.table("quizzes")
        .select("teacher_id")
        .eq("id", str(quiz_id))
        .single()
        .execute()
    )
    if not quiz.data:
        raise HTTPException(status_code=404, detail="Quiz introuvable.")
    if quiz.data["teacher_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Accès refusé.")

    res = (
        supabase.table("quiz_attempts")
        .select("student_name, score, total_questions, submitted_at")
        .eq("quiz_id", str(quiz_id))
        .order("submitted_at", desc=True)
        .execute()
    )
    return res.data