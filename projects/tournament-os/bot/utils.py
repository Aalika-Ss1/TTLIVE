def get_localized_error(data: dict) -> str:
    """Extracts and localizes an error message from a backend DomainError envelope."""
    if not data:
        return "เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ (Unknown error)"
        
    # Check if it's a domain error
    error_dict = data.get("error", {})
    code = error_dict.get("code")
    message = error_dict.get("message")
    
    # If no structured error, try the detail field (from standard FastAPI HTTPExceptions)
    if not code and "detail" in data:
        return data["detail"]
        
    if not code:
        return message or "เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ (Unknown error)"

    # Mapping of domain error codes to Thai messages
    translations = {
        "tournament_not_found": "ไม่พบการแข่งขันนี้ในระบบ",
        "registration_not_open": "ระบบลงทะเบียนยังไม่เปิดหรือปิดไปแล้ว",
        "registration_duplicate": "คุณลงทะเบียนในการแข่งขันนี้ไปแล้ว",
        "game_uid_duplicate": "Game UID นี้ถูกใช้ลงทะเบียนไปแล้วในการแข่งขันนี้",
        "registration_not_found": "ไม่พบข้อมูลการลงทะเบียนของคุณ",
        "check_in_session_not_found": "ไม่พบช่วงเวลาเช็คอิน หรือยังไม่เปิดให้เช็คอิน",
        "check_in_action_invalid": "คำสั่งเช็คอินไม่ถูกต้อง",
        "group_not_found": "คุณยังไม่ได้ถูกจัดกลุ่ม",
        "score_not_found": "ไม่พบข้อมูลคะแนนนี้",
        "score_not_owned": "คุณสามารถรายงานหรือโต้แย้งได้เฉพาะคะแนนของตนเองเท่านั้น",
        "score_not_disputable": "สามารถโต้แย้งได้เฉพาะคะแนนที่ได้รับการอนุมัติแล้ว",
        "dispute_not_found": "ไม่พบคำร้องโต้แย้งคะแนน",
        "stage_required": "จำเป็นต้องระบุ Stage",
        "participant_count_unsupported": "จำนวนผู้เข้าแข่งขันเกินกว่าที่รองรับ",
        "rule_set_missing": "ไม่พบ Rule Set สำหรับการแข่งขันนี้",
        "score_state_invalid": "สถานะของคะแนนในขณะนี้ไม่สามารถทำรายการดังกล่าวได้",
    }
    
    # Return translated message, or fallback to the original English message
    return translations.get(code, message or f"ข้อผิดพลาดระบบ ({code})")
