class IQTestApp:

    def __init__(self):
        self.question = {
            "What is 5+7,?":"12",
            "Waht number comes next : 2,3,4,8,16,?":"32",
            "If All is to 3, then HELLO is to what?":"s",
            "What is the opposite of ODD?": "Even",
            "Which is heavier: 1kg of features or 1 kg of lead?":"NEITHER",
        }


        self.score = 0

    def display_menu(self):
        print("\nIQ Test Menu\n1. Take Test\n2.Show Score\n3.Exit")
        choice = input("Enter choice: ").strip()



        action = {
            "1": self.take_test,
            "2": self.show_score,
            "3": self.exit_app
        }


        action.get(choice, self.invalid)()

    def invalid(self):
        print("Invalid choice, try again.")


    def take_test(self):

        self.score = 0
        for q, a in self.question.items():
            ans = input(q+" ").strip().upper()
            if ans == a:

                self.score += 1

        print(f"Test complete! you scored {self.score}/{len(self.question)}")

    def show_score(self):

        print(f"Current score: {self.score}/{len(self.question)}")

    def exit_app(self):
        print("Goodbye")

        raise SystemExit


if __name__ == "__main__":

    app = IQTestApp()

    while True:

        app.display_menu()



