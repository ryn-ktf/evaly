from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from supabase_client import supabase
from auth import get_current_teacher

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


# ── Schemas ───────────────────────────────────────────────────────────────────

# Each question stored as: { "q": "...", "opts": ["A","B","C","D"], "ans": 0 }
class QuestionItem(BaseModel):
    q: str
    opts: List[str]
    ans: int  # index of correct answer


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

    questions_data = row.get("questions") or []

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
    # store questions as list of dicts
    questions_list = [q.model_dump() for q in body.questions]

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

    questions_list = [q.model_dump() for q in body.questions]

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