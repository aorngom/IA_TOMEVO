import Service_Api from './Service_Api'

const Service_Ocr = {
    analyser: (fichier) => {
        const formData = new FormData()
        formData.append('fichier', fichier)
        return Service_Api.post('/ocr/analyser', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },
    chat: (messages, contexte) =>
        Service_Api.post('/ocr/chat', { messages, contexte }),
}

export default Service_Ocr