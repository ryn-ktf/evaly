from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from supabase_client import supabase

router = APIRouter(prefix="/contact", tags=["contact"])

#kifeh ykon lcontact from rah ymatchi table te db 
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

#simply kima rah mktob ynseri lmessage f table contact_messages w nraj3o success true w message ta3 confirmation, w ila kayn chi error nraj3o error 500 w message ta3 error
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
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi.")

    if not res.data:
        raise HTTPException(status_code=500, detail="Message non sauvegardé.")

    return {
        "success": True,
        "message": f"Merci {body.name}, votre message a bien été envoyé !",
    }
