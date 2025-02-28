document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("upload-form");
    const logList = document.getElementById("log-list");
    const clipList = document.getElementById("clip-list");
    const fullTranscription = document.getElementById("full-transcription");
    const viewProcessingBtn = document.getElementById("view-processing-btn");

    // ✅ Get Video ID from SessionStorage
    let videoId = sessionStorage.getItem("video_id");

    // ✅ Submit video and redirect to processing page
    if (uploadForm) {
        uploadForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            const videoUrl = document.getElementById("video-url").value.trim();
            const clipDuration = document.getElementById("clip-duration").value.trim();
            const clipRanges = document.getElementById("clip-ranges").value.trim();

            if (!videoUrl) {
                alert("Enter a valid YouTube URL!");
                return;
            }

            const payload = {
                url: videoUrl,
                clip_length: parseInt(clipDuration),
                clip_ranges: clipRanges
                    ? clipRanges.split(',').map(range => range.split('-').map(Number))
                    : null
            };

            try {
                const response = await fetch("/submit/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) throw new Error("Failed to submit video.");

                const data = await response.json();
                sessionStorage.setItem("video_id", data.video_id);
                videoId = data.video_id; // ✅ Update video ID
                window.location.href = `/process/`;
            } catch (error) {
                alert("Error submitting video: " + error.message);
            }
        });
    }

    // ✅ Fetch logs in real-time on the index & processing pages
    if (videoId && logList) {
        async function fetchLogs() {
            try {
                const response = await fetch(`/logs/${videoId}/`);
                if (!response.ok) throw new Error("Failed to fetch logs.");

                const data = await response.json();
                logList.innerHTML = data.logs?.map(log => `<li>${log.message}</li>`).join("") || "Processing...";

                // ✅ Auto-redirect to download page when processing is complete
                if (data.logs.some(log => log.message.includes("Processing complete"))) {
                    window.location.href = `/download/`;
                }
            } catch (error) {
                logList.innerHTML = `<li>Error fetching logs: ${error.message}</li>`;
            }
        }

        fetchLogs();
        setInterval(fetchLogs, 5000);
    }

    // ✅ Show "View Processing" button if video is in progress
    if (viewProcessingBtn && videoId) {
        viewProcessingBtn.style.display = "block";
        viewProcessingBtn.addEventListener("click", () => {
            window.location.href = `/process/`;
        });
    }

    // ✅ Fetch Clips & Transcription on download.html
    if (clipList && fullTranscription) {
        async function fetchClips() {
            if (!videoId) {
                clipList.innerHTML = `<p>No video found. Please upload a video first.</p>`;
                return;
            }

            try {
                const response = await fetch(`/clips-and-transcription/${videoId}/`);
                if (!response.ok) throw new Error("Failed to fetch clips.");

                const data = await response.json();
                clipList.innerHTML = data.clips.length > 0
                    ? data.clips.map(clip => {
                        const videoFileName = `${videoId}_clip_${clip.start_time}_${clip.end_time}.mp4`; // ✅ Use video ID + start & end time

                        return `
                            <li>
                                <h3>Clip (${clip.start_time}s - ${clip.end_time}s)</h3>
                                <video controls width="600">
                                    <source src="/media/clips/${videoFileName}" type="video/mp4">
                                    Your browser does not support the video tag.
                                </video>
                                <br>
                                <a href="/media/clips/${videoFileName}" download>
                                    <button>Download Clip</button>
                                </a>
                                <p><strong>Transcript:</strong> ${clip.transcript}</p>
                            </li>
                        `;
                    }).join("")
                    : "<p>No clips found.</p>";
            } catch (error) {
                clipList.innerHTML = `<p>Error loading clips: ${error.message}</p>`;
            }
        }

        async function fetchFullTranscription() {
            if (!videoId) {
                fullTranscription.innerHTML = `<p>No transcription available. Please upload a video first.</p>`;
                return;
            }

            try {
                const response = await fetch(`/full-transcription/${videoId}/`);
                if (!response.ok) throw new Error("Failed to fetch transcription.");

                const data = await response.json();
                fullTranscription.textContent = data.full_transcription || "No transcription available.";
            } catch (error) {
                fullTranscription.innerHTML = `<p>Error fetching transcription: ${error.message}</p>`;
            }
        }

        fetchClips();
        fetchFullTranscription();
    }
});
    
    // The  scripts.js  file contains all the JavaScript code that interacts with the server-side Django views. It handles form submissions, fetches logs in real-time, displays clips and transcriptions, and more. 
    // The JavaScript code is written in vanilla JavaScript and uses the  fetch()  API to make asynchronous requests to the Django server. 
    // Step 8: Create the Django URLs 
    // Next, we need to define the URLs for the Django views we created earlier. 
    // Open the  video_ai/urls.py  file and update it as follows: 
    // # video_ai/urls.py