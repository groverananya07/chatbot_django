from django.shortcuts import render, HttpResponse
from .samchat import ChatBot

chat_obj = ChatBot(profession="Assistant")

def index(request):
    # print(chat_obj.chat_history)
    if request.method == 'POST':
        message = request.POST.get('message')
        # profession=request.POST.get('profession')

        response=chat_obj.ask(message)
        
        # Here, you can save the user data to the database or process it as needed.
        
        # return HttpResponse(response)
        return render(request, 'index.html', {"user_message":message, "messages": response, "chat_history": chat_obj.chat_history})
 
    
    return render(request, 'index.html',{"messages": "Greetings! How can I assist you?"})

