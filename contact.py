from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from supabase_client import supabase
import traceback

router = APIRouter(prefix="/contact", tags=["contact"])

#kifeh ykon contact body ? name, email, subject, message
class ContactBody(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

    @field_validator("name", "subject", "message")
    @classmethod
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError("Ce champ ne peut pas être vide.")
        return v.strip()

# Route pour envoyer un message de contact
@router.post("/", status_code=201)
def send_message(body: ContactBody):
    try:
        res = (
            supabase.table("contact_messages")
            .insert({
                "name":    body.name,
                "email":   body.email,
                "subject": body.subject,
                "message": body.message,
            })
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=500, detail="Message non sauvegardé.")
        return {
            "success": True,
            "message": f"Merci {body.name}, votre message a bien été envoyé !",
        }
    except HTTPException:
        raise
    except Exception as e:
        print("CONTACT ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")