import Service_Api from './Service_Api'

const Service_PaieIA = {
    chat: (messages, sessionId) =>
        Service_Api.post('/paie-ia/chat', {
            messages,
            session_id: sessionId ?? null
        }),
}

export default Service_PaieIA