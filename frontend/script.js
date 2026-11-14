
// ==========================================
// INSIGHTIQ - AI BUSINESS INTELLIGENCE
// ==========================================

// Restore selected dataset
let uploadedTableName =
    localStorage.getItem("uploadedTableName") || null;
// Backend API URL
const API_BASE_URL = "https://insightiq-bi-agent.onrender.com";
// Restore query count
let queryCount =
    Number(localStorage.getItem("queryCount") || 0);

// Store latest query results
let latestChartData = null;
let latestQueryResults = null;
let queryHistory = JSON.parse(
    localStorage.getItem("queryHistory")
) || [];
// ==========================================
// 1. INITIALIZE DASHBOARD
// ==========================================

function initializeDashboard() {

    document.getElementById("kpi-queries").textContent =
        queryCount;

    if (uploadedTableName) {

        document.getElementById("kpi-dataset").textContent =
            "Uploaded";

        const datasetSubtitle = document.querySelector(
            "#kpi-dataset"
        ).parentElement.querySelector("span:last-child");

        datasetSubtitle.textContent = uploadedTableName;
    }

    // Download button starts inactive
    document.getElementById("download-chart").disabled = true;
}

initializeDashboard();


// ==========================================
// 2. UPLOAD CSV / EXCEL DATASET
// ==========================================

async function uploadDataset() {

    const fileInput = document.getElementById("dataset-file");
    const uploadButton = document.getElementById("upload-button");
    const uploadStatus = document.getElementById("upload-status");
    const datasetInfo = document.getElementById("dataset-info");

    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a CSV or XLSX file.");
        return;
    }

    const allowedExtensions = [".csv", ".xlsx"];

    const extension = file.name.substring(
        file.name.lastIndexOf(".")
    ).toLowerCase();

    if (!allowedExtensions.includes(extension)) {
        alert("Only CSV and XLSX files are supported.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadButton.disabled = true;
    uploadStatus.textContent = "Uploading dataset...";
    datasetInfo.textContent = "";

    try {

        const response = await fetch(
            `${API_BASE_URL}/upload-dataset`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Dataset upload failed."
            );
        }

        uploadedTableName = data.table_name;

        localStorage.setItem(
            "uploadedTableName",
            uploadedTableName
        );

        document.getElementById("kpi-dataset").textContent =
            "Uploaded";

        document.querySelector(
            "#kpi-dataset"
        ).parentElement.querySelector(
            "span:last-child"
        ).textContent =
            `${data.rows} records · ${file.name}`;

        uploadStatus.textContent =
            "Dataset uploaded successfully!";

        datasetInfo.replaceChildren();

        const details = [
            ["Dataset", file.name],
            ["Database Table", data.table_name],
            ["Total Records", data.rows],
            ["Columns", data.columns.join(", ")]
        ];

        details.forEach(([label, value]) => {

            const line = document.createElement("p");
            const strong = document.createElement("strong");

            strong.textContent = label + ": ";

            line.appendChild(strong);
            line.appendChild(
                document.createTextNode(String(value))
            );

            datasetInfo.appendChild(line);
        });

        latestChartData = null;

        document.getElementById("download-chart").disabled = true;

        document.getElementById("chart-container").replaceChildren();

        document.getElementById("chart-container").textContent =
            "Ask a question to generate a chart from your new dataset.";

        document.getElementById(
            "chart-recommendation"
        ).classList.remove("show");

    } catch (error) {

        console.error("Upload error:", error);

        uploadStatus.textContent =
            "Unable to upload dataset.";

        datasetInfo.textContent =
            "Error: " + error.message;

    } finally {

        uploadButton.disabled = false;
    }
}


// ==========================================
// 3. ASK AI QUESTION
// ==========================================

async function askQuestion() {

    const questionInput = document.getElementById("question");
    const askButton = document.getElementById("ask-button");
    const loading = document.getElementById("loading");
    const sqlResult = document.getElementById("sql-result");
    const tableContainer = document.getElementById("table-container");
    const errorMessage = document.getElementById("error-message");

    const question = questionInput.value.trim();

    if (!question) {
        alert("Please enter a question.");
        return;
    }

    if (!uploadedTableName) {
        alert("Please upload a dataset first.");
        return;
    }

    askButton.disabled = true;

    // Disable old chart download while a new query runs
    document.getElementById("download-chart").disabled = true;

    loading.textContent =
        "AI Agent is analyzing your question...";

    sqlResult.textContent = "Generating SQL...";
    tableContainer.replaceChildren();
    errorMessage.textContent = "";

    try {

        const response = await fetch(
            `${API_BASE_URL}/ask`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    question: question,
                    table_name: uploadedTableName
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Query execution failed."
            );
        }

        if (!data.success) {
            throw new Error(
                data.error ||
                "The AI agent could not complete the query."
            );
        }

        sqlResult.textContent = data.sql_query;
latestQueryResults = {
    columns: data.columns,
    rows: data.rows
};
saveQueryHistory(
    questionInput.value.trim(),
    data.sql_query
);
        displayResults(data.columns, data.rows);

// Generate AI Business Insights
        await generateAIInsights(
            question,
            data.columns,
            data.rows
        );

        generateChart(data.columns, data.rows);

        queryCount++;

        localStorage.setItem(
            "queryCount",
            queryCount
        );

        document.getElementById("kpi-queries").textContent =
            queryCount;

        loading.textContent =
            "Analysis completed successfully!";

    } catch (error) {

        console.error("Query error:", error);

        errorMessage.textContent =
            "Error: " + error.message;

        loading.textContent =
            "Unable to complete the analysis.";

    } finally {

        askButton.disabled = false;
    }
}


// ==========================================
// 4. DISPLAY QUERY RESULTS IN TABLE
// ==========================================

function displayResults(columns, rows) {
const exportCsvButton = document.getElementById("export-csv");
const exportExcelButton = document.getElementById("export-excel");

const hasResults = rows && rows.length > 0;

exportCsvButton.disabled = !hasResults;
exportExcelButton.disabled = !hasResults;
    const tableContainer =
        document.getElementById("table-container");

    tableContainer.replaceChildren();

    if (!rows || rows.length === 0) {

        tableContainer.textContent = "No records found.";
        return;
    }

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    columns.forEach(column => {

        const th = document.createElement("th");
        th.textContent = column;

        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    rows.forEach(row => {

        const tr = document.createElement("tr");

        row.forEach(value => {

            const td = document.createElement("td");
            td.textContent = value ?? "";

            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    tableContainer.appendChild(table);
}


// ==========================================
// 5. GENERATE INTELLIGENT CHART
// ==========================================

function generateChart(columns, rows) {

    latestChartData = {
        columns: columns,
        rows: rows
    };

    const chartSelector =
        document.getElementById("chart-type");

    if (chartSelector) {
        chartSelector.value = "auto";
    }

    renderChart("auto");
}


// ==========================================
// 6. RENDER SELECTED CHART
// ==========================================

function renderChart(selectedType = "auto") {

    if (!latestChartData) {
        return;
    }

    const columns = latestChartData.columns;
    const rows = latestChartData.rows;

    const chartContainer =
        document.getElementById("chart-container");

    const recommendation =
        document.getElementById("chart-recommendation");

    const downloadButton =
        document.getElementById("download-chart");

    // Disable until the new chart is ready
    downloadButton.disabled = true;

    chartContainer.replaceChildren();

    recommendation.classList.remove("show");
    recommendation.replaceChildren();

    if (!rows || rows.length === 0) {

        chartContainer.textContent =
            "No data available for visualization.";

        return;
    }

    if (typeof Plotly === "undefined") {

        chartContainer.textContent =
            "Chart library could not load. Check your internet connection.";

        return;
    }

    // Identify numeric columns

    const numericColumns = columns
        .map((column, index) => ({
            name: column,
            index: index
        }))
        .filter(col =>
            rows.some(row =>
                row[col.index] !== null &&
                row[col.index] !== "" &&
                Number.isFinite(Number(row[col.index]))
            )
        );

    if (numericColumns.length === 0) {

        chartContainer.textContent =
            "No numeric column found.";

        return;
    }

    const numericColumn = numericColumns[0];
    const numericIndex = numericColumn.index;

    // Identify date/time column

    const dateKeywords =
        /date|time|month|year|day|created|timestamp/i;

    const dateIndex = columns.findIndex((column, index) =>
        index !== numericIndex &&
        (
            dateKeywords.test(column) ||
            (
                rows.length > 0 &&
                rows.every(row =>
                    row[index] !== null &&
                    row[index] !== "" &&
                    !Number.isNaN(Date.parse(row[index]))
                )
            )
        )
    );

    // Identify categorical column

    const categoryIndex = columns.findIndex((column, index) =>
        index !== numericIndex &&
        index !== dateIndex &&
        rows.some(row =>
            row[index] !== null &&
            row[index] !== "" &&
            !Number.isFinite(Number(row[index]))
        )
    );

    // Prepare labels

    let labels;

    if (dateIndex !== -1) {

        labels = rows.map(row =>
            String(row[dateIndex])
        );

    } else if (categoryIndex !== -1) {

        labels = rows.map(row =>
            String(row[categoryIndex])
        );

    } else {

        labels = rows.map((row, index) =>
            `Row ${index + 1}`
        );
    }

    // Prepare numeric values

    const values = rows.map(row =>
        Number(row[numericIndex])
    );

    const categoryName = dateIndex !== -1
        ? columns[dateIndex]
        : categoryIndex !== -1
            ? columns[categoryIndex]
            : "Records";

    const numericName = numericColumn.name;

    // ======================================
    // AUTOMATIC CHART RECOMMENDATION
    // ======================================

    let recommendedType = "bar";
    let recommendationReason = "";

    if (dateIndex !== -1) {

        recommendedType = "line";

        recommendationReason =
            `A line chart is suitable because "${numericName}" is analyzed over time. It helps identify trends and changes across ${categoryName}.`;

    } else if (categoryIndex !== -1) {

        const uniqueCategories = new Set(labels);

        const pieKeywords =
            /category|region|segment|status|type|department/i;

        if (
            uniqueCategories.size >= 2 &&
            uniqueCategories.size <= 6 &&
            pieKeywords.test(categoryName) &&
            values.every(value =>
                Number.isFinite(value) && value >= 0
            )
        ) {

            recommendedType = "pie";

            recommendationReason =
                `A pie chart is suitable because "${numericName}" is compared across ${uniqueCategories.size} categories. It helps show how each category contributes to the whole.`;

        } else {

            recommendedType = "bar";

            recommendationReason =
                `A bar chart is suitable because "${numericName}" is compared across different ${categoryName}. It makes differences between categories easy to understand.`;
        }

    } else {

        recommendationReason =
            `A bar chart is selected to display "${numericName}" across the available records.`;
    }

    // ======================================
    // APPLY USER'S CHART SELECTION
    // ======================================

    let chartType =
        selectedType === "auto"
            ? recommendedType
            : selectedType;

    let manualMessage = "";

    if (
        chartType === "pie" &&
        (
            categoryIndex === -1 ||
            values.some(value =>
                !Number.isFinite(value) || value < 0
            )
        )
    ) {

        chartType = "bar";

        manualMessage =
            "Pie charts require a categorical column and non-negative values. Bar chart is displayed instead.";

        document.getElementById("chart-type").value = "bar";
    }

    // ======================================
    // DISPLAY RECOMMENDATION
    // ======================================

    const heading = document.createElement("h4");
    const explanation = document.createElement("p");

    if (selectedType === "auto") {

        heading.textContent =
            `✨ InsightIQ Recommendation: ${chartType.toUpperCase()} CHART`;

        explanation.textContent =
            recommendationReason;

    } else {

        heading.textContent =
            `📊 Selected Chart: ${chartType.toUpperCase()} CHART`;

        explanation.textContent =
            manualMessage ||
            `You selected a ${chartType} chart. Your existing query results are being displayed using this visualization.`;
    }

    recommendation.appendChild(heading);
    recommendation.appendChild(explanation);
    recommendation.classList.add("show");

    // ======================================
    // BUILD CHART TRACE
    // ======================================

    let trace;

    if (chartType === "pie") {

        trace = {
            labels: labels,
            values: values,
            type: "pie",
            hole: 0.35,
            textinfo: "label+percent",
            hovertemplate:
                "%{label}<br>%{value}<extra></extra>"
        };

    } else if (chartType === "line") {

        trace = {
            x: labels,
            y: values,
            type: "scatter",
            mode: "lines+markers",
            line: {
                color: "#7657e8",
                width: 3
            },
            marker: {
                size: 7
            },
            hovertemplate:
                "%{x}<br>%{y}<extra></extra>"
        };

    } else {

        trace = {
            x: labels,
            y: values,
            type: "bar",
            marker: {
                color: "#7657e8"
            },
            hovertemplate:
                "%{x}<br>%{y}<extra></extra>"
        };
    }

    // ======================================
    // CHART LAYOUT
    // ======================================

    const layout = {

        title: {
            text: `${numericName} by ${categoryName}`,
            font: {
                size: 16,
                color: "#20283a"
            },
            x: 0.03
        },

        xaxis: {
            title: chartType === "pie" ? "" : categoryName,
            automargin: true
        },

        yaxis: {
            title: chartType === "pie" ? "" : numericName,
            rangemode: "tozero"
        },

        paper_bgcolor: "#ffffff",
        plot_bgcolor: "#ffffff",

        margin: {
            l: 65,
            r: 25,
            t: 65,
            b: 65
        },

        font: {
            family: "Inter, sans-serif",
            color: "#8992a5"
        }
    };

    const config = {
        responsive: true,
        displaylogo: false
    };

    // ======================================
    // CREATE CHART AND ENABLE DOWNLOAD
    // ======================================

    Plotly.newPlot(
        chartContainer,
        [trace],
        layout,
        config
    )
    .then(() => {

        // Enable only after successful chart rendering
        downloadButton.disabled = false;

        console.log("Chart rendered successfully.");

    })
    .catch(error => {

        console.error("Chart rendering failed:", error);

        downloadButton.disabled = true;

        chartContainer.textContent =
            "Unable to render chart. Please try another query.";
    });

    console.log(
        "InsightIQ selected chart type:",
        chartType
    );
}


// ==========================================
// 7. INTERACTIVE CHART SELECTOR
// ==========================================

document.getElementById("chart-type").addEventListener(
    "change",
    function() {

        const selectedType = this.value;

        if (!latestChartData) {

            alert("Please run a query before selecting a chart.");

            this.value = "auto";
            return;
        }

        renderChart(selectedType);
    }
);


// ==========================================
// 8. PRESS ENTER TO ASK AI
// ==========================================

document.getElementById("question").addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter" && !event.shiftKey) {

            event.preventDefault();
            askQuestion();
        }
    }
);


// ==========================================
// 9. DOWNLOAD CHART AS PNG
// ==========================================

document.getElementById("download-chart").addEventListener(
    "click",
    function() {

        const chartContainer =
            document.getElementById("chart-container");

        if (
            !latestChartData ||
            !chartContainer.data ||
            this.disabled
        ) {
            alert("Please generate a chart first.");
            return;
        }

        Plotly.downloadImage(
            chartContainer,
            {
                format: "png",
                filename: "insightiq-chart",
                width: 1200,
                height: 700,
                scale: 2
            }
        )
        .catch(error => {

            console.error("Download failed:", error);

            alert("Unable to download chart. Please try again.");
        });
    }
);
// ==========================================
// EXPORT QUERY RESULTS AS CSV
// ==========================================

function exportCSV() {

    if (!latestQueryResults) {
        alert("No query results available to export.");
        return;
    }

    const columns = latestQueryResults.columns;
    const rows = latestQueryResults.rows;

    const escapeCSV = (value) => {
        const text = value === null || value === undefined
            ? ""
            : String(value);

        return `"${text.replace(/"/g, '""')}"`;
    };

    const csvContent = [
        columns.map(escapeCSV).join(","),
        ...rows.map(row => row.map(escapeCSV).join(","))
    ].join("\n");

    const blob = new Blob(
        ["\uFEFF" + csvContent],
        { type: "text/csv;charset=utf-8;" }
    );

    const link = document.createElement("a");

    link.href = URL.createObjectURL(blob);
    link.download = "insightiq-query-results.csv";

    link.click();

    URL.revokeObjectURL(link.href);
}
// Connect CSV Export Button

document.getElementById("export-csv")
    .addEventListener("click", exportCSV);

// ==========================================
// EXPORT QUERY RESULTS AS EXCEL
// ==========================================

function exportExcel() {

    if (!latestQueryResults) {
        alert("No query results available to export.");
        return;
    }

    if (typeof XLSX === "undefined") {
        alert("Excel library not loaded. Please check your internet connection.");
        return;
    }

    const columns = latestQueryResults.columns;
    const rows = latestQueryResults.rows;

    const worksheetData = [
        columns,
        ...rows
    ];

    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);

    const workbook = XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(
        workbook,
        worksheet,
        "Query Results"
    );

    XLSX.writeFile(
        workbook,
        "insightiq-query-results.xlsx"
    );
}
// Connect Excel Export Button

document.getElementById("export-excel")
    .addEventListener("click", exportExcel);


// ==========================================

function saveQueryHistory(question, sqlQuery) {

    const historyItem = {
        question: question,
        sqlQuery: sqlQuery,
        date: new Date().toLocaleString()
    };

    queryHistory.unshift(historyItem);

    // Keep only the latest 20 queries
    queryHistory = queryHistory.slice(0, 20);

    // Save history in browser storage
    localStorage.setItem(
        "queryHistory",
        JSON.stringify(queryHistory)
    );

    // Refresh the history display
    displayQueryHistory();
}

// ==========================================
// DISPLAY QUERY HISTORY
// ==========================================

function displayQueryHistory() {

    const historyContainer = document.getElementById(
        "query-history-container"
    );

    if (!historyContainer) {
        return;
    }

    historyContainer.replaceChildren();

    if (!queryHistory || queryHistory.length === 0) {

        const emptyMessage = document.createElement("p");

        emptyMessage.className = "empty-state";
        emptyMessage.textContent =
            "Your previous queries will appear here.";

        historyContainer.appendChild(emptyMessage);

        return;
    }

    queryHistory.forEach((item, index) => {

        const historyItem = document.createElement("div");
        historyItem.className = "history-item";

        const questionTitle = document.createElement("h4");
        questionTitle.textContent = item.question;

        const dateText = document.createElement("p");
        dateText.textContent = item.date;

        const runButton = document.createElement("button");
        runButton.className = "history-run-button";
        runButton.dataset.index = index;
        runButton.textContent = "Run Again";

        historyItem.appendChild(questionTitle);
        historyItem.appendChild(dateText);
        historyItem.appendChild(runButton);

        historyContainer.appendChild(historyItem);
    });
}


// ==========================================
// RUN PREVIOUS QUERY AGAIN
// ==========================================

const historyContainer = document.getElementById(
    "query-history-container"
);

if (historyContainer) {

    historyContainer.addEventListener("click", function(event) {

        const button = event.target.closest(
            ".history-run-button"
        );

        if (!button) return;

        const index = Number(button.dataset.index);
        const selectedQuery = queryHistory[index];

        if (!selectedQuery) return;

        document.getElementById("question").value =
            selectedQuery.question;

        askQuestion();
    });
}


// ==========================================
// LOAD HISTORY WHEN DASHBOARD OPENS
// ==========================================

displayQueryHistory();

async function generateAIInsights(question, columns, rows) {

    const insightsContainer =
        document.getElementById("ai-insights");

    insightsContainer.textContent =
        "Generating AI business insights...";

    try {

        const response = await fetch(
            `${API_BASE_URL}/generate-insights`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: question,
                    columns: columns,
                    rows: rows
                })
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error ||
                data.detail ||
                "Unable to generate insights."
            );
        }

        const insights = data.insights;

        insightsContainer.replaceChildren();

        const sections = [
            ["Key Finding", insights.key_finding],
            ["Business Insight", insights.business_insight],
            ["Recommendation", insights.recommendation]
        ];

        sections.forEach(([heading, content]) => {

            const block = document.createElement("div");

            const title = document.createElement("h3");
            title.textContent = heading;

            const paragraph = document.createElement("p");
            paragraph.textContent = content;

            block.append(title, paragraph);

            insightsContainer.appendChild(block);
        });

    } catch (error) {

        console.error("Insight generation error:", error);

        insightsContainer.textContent =
            "Unable to generate business insights. Your query results are still available.";
    }
}
