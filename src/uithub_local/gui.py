HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>uithub-local | Repository flattener</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #050505;
            color: #ededed;
        }
        .glass {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .glow:hover {
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
        }
        input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 1px #3b82f6;
        }
        .shimmer {
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
            background-size: 200% 100%;
            animation: shimmer 2s infinite;
        }
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
    </style>
</head>
<body class="flex flex-col min-h-screen items-center justify-center p-4">
    <div class="w-full max-w-2xl">
        <!-- Header -->
        <div class="text-center mb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <h1 class="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent mb-2">
                uithub-local
            </h1>
            <p class="text-neutral-500 text-sm">
                Flatten any GitHub repository into context-ready dumps for LLMs.
            </p>
        </div>

        <!-- Main Card -->
        <div class="glass rounded-2xl p-8 shadow-2xl relative overflow-hidden">
            <div id="loader" class="hidden absolute top-0 left-0 w-full h-1 shimmer"></div>
            
            <form id="dumpForm" class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                        <label class="text-xs font-semibold text-neutral-400 uppercase tracking-wider">GitHub User</label>
                        <input type="text" id="user" placeholder="google" required
                            class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm transition-all focus:bg-white/10">
                    </div>
                    <div class="space-y-2">
                        <label class="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Repository</label>
                        <input type="text" id="repo" placeholder="gemini-cli" required
                            class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm transition-all focus:bg-white/10">
                    </div>
                </div>

                <!-- Advanced Options Toggle -->
                <button type="button" onclick="toggleAdvanced()" 
                    class="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1 group">
                    <i data-lucide="settings-2" class="w-3 h-3 group-hover:rotate-45 transition-transform"></i>
                    Advanced Options
                </button>

                <div id="advanced" class="hidden space-y-4 pt-2 border-t border-white/5 animate-in fade-in duration-300">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <label class="text-xs text-neutral-400">Include patterns</label>
                            <input type="text" id="include" value="*" 
                                class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:bg-white/10">
                        </div>
                        <div class="space-y-2">
                            <label class="text-xs text-neutral-400">Exclude patterns</label>
                            <input type="text" id="exclude" placeholder="tests/, docs/"
                                class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:bg-white/10">
                        </div>
                        <div class="space-y-2">
                            <label class="text-xs text-neutral-400">Split tokens</label>
                            <input type="number" id="split" placeholder="e.g. 50000"
                                class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:bg-white/10">
                        </div>
                        <div class="space-y-2">
                            <label class="text-xs text-neutral-400">Format</label>
                            <select id="format" class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:bg-white/10 appearance-none">
                                <option value="text">Plain Text</option>
                                <option value="json">JSON</option>
                                <option value="html">HTML</option>
                            </select>
                        </div>
                    </div>
                    <div class="flex items-center gap-4">
                        <label class="flex items-center gap-2 cursor-pointer group">
                            <input type="checkbox" id="exclude_comments" class="hidden peer">
                            <div class="w-4 h-4 rounded border border-white/20 peer-checked:bg-blue-600 peer-checked:border-blue-600 transition-all"></div>
                            <span class="text-xs text-neutral-400 group-hover:text-neutral-200 transition-colors">Exclude Comments</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer group">
                            <input type="checkbox" id="not_ignore" class="hidden peer">
                            <div class="w-4 h-4 rounded border border-white/20 peer-checked:bg-blue-600 peer-checked:border-blue-600 transition-all"></div>
                            <span class="text-xs text-neutral-400 group-hover:text-neutral-200 transition-colors">Ignore .gitignore</span>
                        </label>
                    </div>
                </div>

                <div class="pt-4">
                    <button type="submit" id="submitBtn"
                        class="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 rounded-xl transition-all glow flex items-center justify-center gap-2 shadow-lg shadow-blue-900/20 active:scale-95">
                        <i data-lucide="download" class="w-4 h-4"></i>
                        Generate Dump
                    </button>
                </div>
            </form>
        </div>

        <!-- Footer -->
        <div class="mt-8 flex justify-center gap-6">
            <a href="/docs" class="text-xs text-neutral-600 hover:text-neutral-400 transition-colors flex items-center gap-1">
                <i data-lucide="book-open" class="w-3 h-3"></i>
                API Docs
            </a>
            <a href="https://github.com/ramgeart/uithub-local" target="_blank" class="text-xs text-neutral-600 hover:text-neutral-400 transition-colors flex items-center gap-1">
                <i data-lucide="github" class="w-3 h-3"></i>
                GitHub
            </a>
        </div>
    </div>

    <script>
        lucide.createIcons();

        function toggleAdvanced() {
            const adv = document.getElementById('advanced');
            adv.classList.toggle('hidden');
        }

        document.getElementById('dumpForm').onsubmit = async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('submitBtn');
            const loader = document.getElementById('loader');
            
            const user = document.getElementById('user').value;
            const repo = document.getElementById('repo').value;
            const format = document.getElementById('format').value;
            const split = document.getElementById('split').value;
            const include = document.getElementById('include').value;
            const exclude = document.getElementById('exclude').value;
            const exclude_comments = document.getElementById('exclude_comments').checked;
            const not_ignore = document.getElementById('not_ignore').checked;

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Processing...';
            loader.classList.remove('hidden');
            lucide.createIcons();

            try {
                const url = new URL(`/dump/${user}/${repo}`, window.location.origin);
                url.searchParams.append('format', format);
                if (split) url.searchParams.append('split', split);
                if (include) url.searchParams.append('include', include);
                if (exclude) url.searchParams.append('exclude', exclude);
                if (exclude_comments) url.searchParams.append('exclude_comments', 'true');
                if (not_ignore) url.searchParams.append('not_ignore', 'true');

                const response = await fetch(url);
                if (!response.ok) throw new Error(await response.text());

                // For downloads
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = downloadUrl;
                const ext = format === 'json' ? 'json' : (format === 'html' ? 'html' : 'txt');
                a.download = `${repo}_dump.${ext}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(downloadUrl);
            } catch (err) {
                alert('Error: ' + err.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i data-lucide="download" class="w-4 h-4"></i> Generate Dump';
                loader.classList.add('hidden');
                lucide.createIcons();
            }
        };
    </script>
</body>
</html>
"""
