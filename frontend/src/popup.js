async function fetchRAG() {
  const question = "What should I reply?"; // Replace with dynamic input if needed

  try {
      const response = await fetch("http://localhost:8000/rag", {
          method: "POST",
          headers: {
              "Content-Type": "application/json",
          },
          body: JSON.stringify({ question }),
      });

      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      displayRecommendation(data.rag_answer);
  } catch (error) {
      console.error("Failed to fetch RAG recommendation:", error);
  }
}

function displayRecommendation(recommendation) {
  const suggestionList = document.getElementById("suggestionList");
  suggestionList.innerHTML = ""; // Clear previous suggestions

  const listItem = document.createElement("li");
  listItem.textContent = recommendation;
  suggestionList.appendChild(listItem);
}
