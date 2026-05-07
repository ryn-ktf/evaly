from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr #for email validation
from supabase_client import supabase

router = APIRouter(prefix="/auth", tags=["auth"]) 
bearer = HTTPBearer()



 #request ykon fih both hedo 
class LoginBody(BaseModel):
    email: EmailStr
    password: str


#extract token mn request w tvaldi maa supabase w traja3 user details ila token sahih w valid, w ila token invalid traja3 error 401
def get_current_teacher(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        user = supabase.auth.get_user(creds.credentials)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Token invalide.")
        return user.user
    except Exception:
        raise HTTPException(status_code=401, detail="Non autorisé.")


#ndiro login  wycheki lpassword w email w nraj3o token ila credentials sahihin, w ila ghalta nraj3o error 401
@router.post("/login")
def login(body: LoginBody):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
    except Exception as e:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    if not response.session:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    return {
        "access_token": response.session.access_token,
        "teacher_id": response.user.id,
        "email": response.user.email,
    }


#simply ndiro logout w nsignout mn supabase w nraj3o success true,
@router.post("/logout")
def logout(current_user=Depends(get_current_teacher)):
    supabase.auth.sign_out()
    return {"success": True}
