import socket
import sys
import time
import select
import random
import requests

MAXIMUM_PARTICIPANTS = 4
clients = []
client_addresses = {}
names = {}
scores = {}
max_score = 0

# Function to fetch questions from the Open Trivia API
def get_questions_from_api():
    url = "https://opentdb.com/api.php"  # API endpoint
    
    params = {
        "amount": 5,
        "type": "multiple",
        "difficulty": "easy",
        "category": 19
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["response_code"] == 0:
                results = data["results"]
                question_list = [result["question"] for result in results]
                opt_list_ = [result["incorrect_answers"] + [result["correct_answer"]] for result in results]
                ans_list_ = [result["correct_answer"] for result in results]
                opt_list = []
                ans_list = []
                for i in range(len(ans_list_)):
                    opts = opt_list_[i]
                    ans = ans_list_[i]
                    random.shuffle(opts)
                    formatted_opts = ""
                    for j, option in enumerate(opts):
                        formatted_opts += f"{chr(97+j)}) {option}  \n\t"
                    opt_list.append(formatted_opts)
                    ans_list.append(chr(97 + opts.index(ans)))

                return tuple(question_list), tuple(opt_list), tuple(ans_list)
            else:
                print("No questions found in the API response")
        else:
            print("Failed to fetch questions from API")
    except requests.exceptions.RequestException as e:
        print("Error fetching questions:", str(e))
# Call the function to get questions from the Open Trivia API
question_list, opt_list, ans_list = get_questions_from_api()



# def create_socket():
#     try:
#         global host
#         global port
#         global server_socket
#         host = "10.0.2.15"
#         port = 9999
#         server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#     except socket.error as msg:
#         print("Socket creation error: " + str(msg))



# # Binding the socket and listening for connections
# def bind_socket():
#     try:
#         global host
#         global port
#         global server_socket
#         print("\tBinding the Port: " + str(port))

#         server_socket.bind((host, port))
#         server_socket.listen(5)

#     except socket.error as msg:
#         print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
#         bind_socket()



# Handling connection from multiple clients and saving to a list
def accepting_connections():

    #giving just 10 seconds to the clients to establish the connection
    #settimeout will turn off the socket after 10 seconds
    print("\t10 SECONDS FOR THE PARTICIPANTS TO JOIN\n")
    server_socket.settimeout(12)
    number_of_clients = 0
    while True:
        try:
            connection, address = server_socket.accept()

            clients.append(connection)
            client_addresses[connection] = address
            number_of_clients += 1
            print("\t" + address[0] + " joined the game!")
            if number_of_clients >= MAXIMUM_PARTICIPANTS:
                break

        except socket.timeout as e:
            print('\n\tNO CONNECTIONS AFTER 10 SECONDS...')
            server_socket.close()
            break


    #if there are less than 2 participants
    if(len(clients) <= 1):
        print(f"\tNeed at least 2 participants, {len(clients)} joined")
        sys.exit();


    print("\n");



    #if they send nothing then the error will occur which we will pass
    for i, connection in enumerate(clients):
        player_id = "Player"+str(i+1)

        connection.send(player_id.encode("utf-8"))
        names[connection] = player_id
        print("\tPlayer id set for " + client_addresses[connection][0] + " as "+player_id)


    #if all names are given for the connections start the game
    print("\tAll ids given to the players, lets start the game in 5 seconds\n")


    #This is to ensure that game starts at the same time for everyone.
    #When this y will reach the other side, it will signal to start game
    time.sleep(5)
    for i in clients:
        i.send("y".encode("utf-8"))
        scores[i] = 0




# FUNCTION TO CLEAR THE SOCKET
def clear_socket(sock):

    i, o, e = select.select([sock],[],[], 1)
    if (i):
        ans = sock.recv(2048)
        # print("\ti ate up ", ans)




#function to tell if the buzzer is pressed and who pressed the buzzer first
def buzzer(time):
    for client in clients:
        client.setblocking(0)

    i, o, e = select.select(clients, [], [], time+2)

    if(i):
        buzz = i[0].recv(2048).decode("utf-8")
        print("\tbuzzer : ", buzz)
        i[0].send("Yes".encode("utf-8"))

        for client in clients:
            if(client != i[0]):
                client.send(f"No{names[i[0]]}".encode("utf-8"))

        return [True, i[0]]

    else:
        return [False, 1]




# IT ACCEPTS THE ANSWER AND GIVES THE SCORE TO THE BUZZER PRESSER 
def evaluator(who_buzzed, question_no, time):
    i, o, e = select.select([who_buzzed], [], [], time)

    if(i):
        ans = who_buzzed.recv(2048).decode("utf-8")
        print("\t--> Answer : ", ans, "\n\n")

        if ans[0] == ans_list[question_no][0]:
            scores[who_buzzed] += 1
            who_buzzed.send("Correct Answer!!!!, You earn 1 point".encode("utf-8"))
        else:
            scores[who_buzzed] -= 0.5
            who_buzzed.send("Wrong Answer :(, You lose 0.5 points".encode("utf-8"))
    else:
        scores[who_buzzed] -= 0.5
        who_buzzed.send("You failed to answer it in time, You lose 0.5 points".encode("utf-8"))



# THIS FUNCTION SIGNALS THE END OF THE QUESTION TIME TO EVERY CLIENT
def display_score(sig, scorecard):
    key = "mv"
    if(sig == 0):
        key = "end"
    for i in clients:
        i.send((key+str(scores[i]) + "\n\n" + "\tSCORECARD : \n\n" + scorecard).encode("utf-8"))



########################################
# THE MAIN PROGRAM STARTS FROM HERE ON #
########################################

try:
    host = "10.0.2.15"
    port = 9999
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("\tBinding the Port: " + str(port))
    server_socket.bind((host, port))
    server_socket.listen(5)
    accepting_connections()
    flag = True

except socket.error as msg:
    print("Socket creation error: " + str(msg))
    flag =  False


if flag:

    for question_num in range(len(question_list)):
        # Print the question
        time.sleep(1)
        print(f"\tQUES {question_num+1} :-")
        print(f"\n\t-----> {question_list[question_num]}\n\t{opt_list[question_num]}")


        #sending question to everyone
        for j in clients:
            j.send(f"QUES {question_num+1} :-\n-----> {question_list[question_num]}\n\t{opt_list[question_num]}".encode("utf-8"))
        time.sleep(2)


        # It will contain whether the buzzer is pressed and who pressed it
        press = buzzer(10)


        if(press[0]):
            evaluator(press[1], question_num, 10)
            print(f"\t{names[press[1]]} PRESSED THE BUZZER FIRST\n")
        else:
            print("\tBUZZER NOT PRESSED IN TIME, time to move to the next question\n")
            for conn in clients:
                conn.send("wastesig".encode("utf-8"))

        time.sleep(5)



        print("\tAfter completion of question :-\n")
        time.sleep(2)


        scorecard = ""
        scorecard += "\t{0:20} {1:20} {2}\n".format("ADDRESS", "NAME", "SCORE")
        for conn in clients:
            scorecard += "\t{0:20} {1:20} {2}\n".format(client_addresses[conn][0], names[conn], scores[conn])
        scorecard += "\n\n"

        print(scorecard)
        time.sleep(4)
        max_score = 0
        for cli in clients:
            if scores[cli] > max_score:
                max_score = scores[cli]

        if(question_num == len(question_list)-1):
            display_score(0, scorecard)      
            for conn in clients:
                if conn == press[1]:
                    continue
                clear_socket(conn)
            break
        else:
            display_score(1, scorecard)
            for conn in clients:
                if conn == press[1]:
                    continue
                clear_socket(conn)

        time.sleep(1)

    for conn in clients:
            if(scores[conn] == max_score):
                conn.send(f"Congrats! You won the game. Your score is {scores[conn]}".encode("utf-8"))
            else:
                conn.send(f"You lost the game. Your score is {scores[conn]}".encode('utf-8'))


    # for conn in clients:
    #     if(conn == winner):
    #         conn.send(f"Congrats! You won the game. Your score is {scores[conn]}".encode("utf-8"))
    #     else:
    #         if(winner):
    #             conn.send(f"You lost the game. Your score is {scores[conn]}".encode('utf-8'))
    #         else:
    #             conn.send(f"The game is tied. Your score is {scores[conn]}".encode('utf-8'))


    time.sleep(10)
    server_socket.close()
    for i in clients:
        i.close()