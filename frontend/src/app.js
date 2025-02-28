// @ts-nocheck

const agent1Btn = document.querySelector("#agent_1");
const agent2Btn = document.querySelector("#agent_2");
const chatMessages = document.querySelector(".chat-messages");
const chatInputForm = document.querySelector("form");
const chatInput = document.querySelector("input[type='text']");
const sendButton = document.querySelector("button");
const clearChatBtn = document.querySelector(".clear-chat-button"); // Add the Clear Chat button selector

let messages = [];

// Fetch filtered_data.json and populate the messages array
const loadMessages = async () => {
  try {
    const response = await fetch("filtered_data.json");
    const data = await response.json();
    messages = data.map((msg) => ({
      sender: msg.agent === "agent_1" ? "Agent 1" : "Agent 2",
      text: msg.message,
    }));
    renderMessages();
  } catch (error) {
    console.error("Error loading messages:", error);
  }
};

// Initial load of messages
window.onload = loadMessages;

let messageSender = "Agent 1";
let isAgent1Active = true; // Default: Agent 1 starts as sender

const createChatMessageElement = (message) => `
  <div class="flex items-center space-x-2 ${message.sender === messageSender ? "justify-end" : "justify-start"}">
    ${message.sender !== messageSender ? '<div class="w-8 h-8 bg-slate-100 rounded-full"></div>' : ""}
    <div class="bg-slate-100 p-2 rounded-xl max-w-xs">
      <p>${message.text}</p>
    </div>
    ${message.sender === messageSender ? '<div class="w-8 h-8 bg-slate-100 rounded-full"></div>' : ""}
  </div>
`;

const renderMessages = () => {
  chatMessages.innerHTML = messages.map(createChatMessageElement).join("");
};

const updateMessageSender = (name) => {
  messageSender = name;
  isAgent1Active = name === "Agent 1";

  if (isAgent1Active) {
    agent1Btn.classList.remove("bg-slate-100");
    agent1Btn.classList.add("bg-blue-500", "text-white");
    agent2Btn.classList.remove("bg-blue-500", "text-white");
    agent2Btn.classList.add("bg-slate-100");
  } else {
    agent2Btn.classList.remove("bg-slate-100");
    agent2Btn.classList.add("bg-blue-500", "text-white");
    agent1Btn.classList.remove("bg-blue-500", "text-white");
    agent1Btn.classList.add("bg-slate-100");
  }

  chatInput.placeholder = `Type a message as ${messageSender}...`;
  renderMessages();
};

agent1Btn.onclick = () => updateMessageSender("Agent 1");
agent2Btn.onclick = () => updateMessageSender("Agent 2");

const sendMessage = (e) => {
  e.preventDefault();

  if (!chatInput.value.trim()) return;

  const message = {
    sender: messageSender,
    text: chatInput.value,
  };

  messages.push(message);
  localStorage.setItem("messages", JSON.stringify(messages));

  renderMessages();

  chatInput.value = "";
  chatMessages.scrollTop = chatMessages.scrollHeight;
};

sendButton.addEventListener("click", sendMessage);
chatInputForm.addEventListener("submit", sendMessage);

clearChatBtn.addEventListener("click", () => {
  messages.length = 0;
  localStorage.removeItem("messages");
  renderMessages();
});

document.addEventListener('DOMContentLoaded', () => {
  const recommendationButton = document.getElementById('recommendationButton');
  const suggestionList = document.getElementById('suggestionList');

  recommendationButton.addEventListener('click', async () => {
      try {
          const response = await fetch('http://localhost:8000/rag', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({ question: 'What are your recommendations?' }),
          });

          if (!response.ok) {
              throw new Error('Network response was not ok');
          }

          const data = await response.json();
          const recommendations = data.rag_answer;

          suggestionList.innerHTML = '';
          recommendations.forEach((recommendation) => {
              const listItem = document.createElement('li');
              listItem.textContent = recommendation;
              suggestionList.appendChild(listItem);
          });
      } catch (error) {
          console.error('There has been a problem with your fetch operation:', error);
      }
  });
});

// Function to fetch reply suggestions from the RAG endpoint
async function fetchRAG() {
  try {
      // Static question asking for reply suggestions based on the conversation context
      const staticQuestion = "Give several recommendation on how I would continue the conversation";
      
      console.log("Sending static question to RAG endpoint:", staticQuestion);
      
      // Make the API call to the RAG endpoint
      const response = await fetch('http://localhost:8000/rag', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({
              question: staticQuestion
          })
      });
      
      if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Log the response to console
      console.log("RAG Response:", data);
      
      // Also display in the suggestion list for visibility
      const suggestionList = document.getElementById('suggestionList');
      if (suggestionList) {
          suggestionList.innerHTML = `<li class="p-3 bg-blue-50 rounded-lg">${data.rag_answer}</li>`;
      }
      
  } catch (error) {
      console.error('Error fetching RAG recommendations:', error);
  }
}

// Add event listener to the recommendation button
document.addEventListener('DOMContentLoaded', () => {
  const recommendationButton = document.getElementById('recommendationButton');
  if (recommendationButton) {
      recommendationButton.addEventListener('click', fetchRAG);
  }
});