// App.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TeamSelector from './components/TeamSelector.jsx';
import teamLogos from './assets/teamLogos.js';

const defaultMessages = [
    "Calculating Mbappé's offsides...",
    "Counting the number of times Lamine Yamal cut inside...",
    "Analyzing Vinícius Jr.'s dribbles...",
    "Tallying Rodrygo's sprints...",
    "Measuring Pedri's touches..."
];

function LoadingScreen({ progress }) {
    const [msgIndex, setMsgIndex] = useState(0);

    useEffect(() => {
        const msgInterval = setInterval(() => {
        setMsgIndex(i => (i + 1) % defaultMessages.length);
        }, 2000);
        return () => clearInterval(msgInterval);
    }, []);

    return (
        <div className="fixed inset-0 bg-gray-700 flex flex-col items-center justify-center z-50">
        <div className="text-2xl font-semibold text-gray-200 mb-4">
            Loading La Liga Data...
        </div>
        <div className="overflow-hidden whitespace-nowrap w-full text-center mb-6 text-gray-400">
            <div className="inline-block animate-marquee">
            {defaultMessages[msgIndex]}
            </div>
        </div>
        <div className="w-3/4 bg-gray-600 h-2 rounded-full overflow-hidden">
            <div
            className="h-2 bg-[#E30613] transition-all duration-100"
            style={{ width: `${progress}%` }}
            />
        </div>
        </div>
    );
}

export default function App() {
    const [teams, setTeams] = useState([]);
    const [teamId, setTeamId] = useState('');
    const [nextFixtures, setNextFixtures] = useState([]);
    const [lastFixtures, setLastFixtures] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [progress, setProgress] = useState(0);

    // Always show 6-second loader, fetch teams in background
    useEffect(() => {
        const start = Date.now();
        const timer = setInterval(() => {
        const elapsed = Date.now() - start;
        setProgress(Math.min(100, (elapsed / 6000) * 100));
        }, 100);

        const timeout = setTimeout(() => {
        clearInterval(timer);
        setProgress(100);
        setIsLoading(false);
        }, 6000);

        axios
        .get('/api/teams')
        .then(res => setTeams(res.data))
        .catch(err => console.error('Error fetching teams:', err));

        return () => {
        clearInterval(timer);
        clearTimeout(timeout);
        };
    }, []);

    useEffect(() => {
        if (!teamId) {
        setNextFixtures([]);
        setLastFixtures([]);
        return;
        }

        axios
        .get(`/api/fixtures/next/${teamId}`)
        .then(res => setNextFixtures(Array.isArray(res.data) ? res.data : []))
        .catch(() => setNextFixtures([]));

        axios
        .get(`/api/fixtures/last/${teamId}`)
        .then(res => setLastFixtures(Array.isArray(res.data) ? res.data : []))
        .catch(() => setLastFixtures([]));
    }, [teamId]);

    if (isLoading) {
        return <LoadingScreen progress={progress} />;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-800 to-gray-100 p-8">
        <div className="max-w-4xl mx-auto">
            <h1 className="text-4xl font-extrabold text-gray-200 mb-8 text-center">
            ⚽ La Liga Predictor
            </h1>

            {/* Team Selector */}
            <div className="bg-gray-400 rounded-2xl shadow-2xl border-t-4 border-[#E30613] p-8 mb-10">
            <TeamSelector
                label="Select Team"
                teams={teams}
                selectedTeam={teamId}
                onChange={setTeamId}
            />
            </div>

            {/* —— Next 5 Fixture Predictions (Grid) —— */}
            <div className="mt-6 bg-gray-400 rounded-2xl shadow-2xl border-t-4 border-[#E30613] p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
                Next 5 Fixture Predictions
            </h2>

            {teamId ? (
                nextFixtures.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {nextFixtures.map((m, i) => {
                    // Determine human‐friendly prediction and confidence
                    const labels = ['Home Win', 'Draw', 'Away Win'];
                    const resultIndex = labels.indexOf(m.prediction.result);
                    const conf = m.prediction.confidence?.[resultIndex] ?? 0;
                    const predLabel =
                        m.prediction.result === 'Home Win'
                        ? `${m.home} to win`
                        : m.prediction.result === 'Away Win'
                        ? `${m.away} to win`
                        : 'Draw';

                    return (
                        <div
                        key={i}
                        className="bg-gray-400 rounded-lg shadow-md p-4 flex flex-col items-center"
                        >
                        {/* Home Crest */}
                        <img
                            src={teamLogos[m.home]}
                            alt={m.home}
                            className="w-16 h-16 mb-2"
                        />
                        <div className="text-center mb-2">
                            <p className="text-xs text-gray-600">Home</p>
                            <p className="font-medium">{m.home}</p>
                        </div>

                        {/* Prediction */}
                        <div className="bg-gray-300 rounded-full px-4 py-2 mb-2 border">
                            <p className="text-[#E30613] font-semibold">
                            {predLabel}
                            </p>
                            <p className="text-sm text-gray-600">
                            ({(conf * 100).toFixed(1)}%)
                            </p>
                        </div>

                        <div className="text-center mt-2">
                            <p className="text-xs text-gray-600">Away</p>
                            <p className="font-medium">{m.away}</p>
                        </div>
                        {/* Away Crest */}
                        <img
                            src={teamLogos[m.away]}
                            alt={m.away}
                            className="w-16 h-16 mt-2"
                        />

                        {/* Date */}
                        <p className="mt-4 text-sm text-gray-600">
                            {new Date(m.utcDate).toLocaleDateString()}
                        </p>
                        </div>
                    );
                    })}
                </div>
                ) : (
                <p className="text-gray-600 italic">No upcoming matches scheduled.</p>
                )
            ) : (
                <p className="text-gray-500 italic">
                Select a team to view upcoming fixtures.
                </p>
            )}
            </div>

            {/* —— Last 5 Results (Grid) —— */}
            <div className="mt-6 bg-gray-400 rounded-2xl shadow-2xl border-t-4 border-[#E30613] p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
                Last 5 Results
            </h2>

            {teamId ? (
                lastFixtures.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {lastFixtures.map((m, i) => {
                    // Compute human‐friendly predLabel and confidence
                    const labels = ['Home Win', 'Draw', 'Away Win'];
                    const resultIndex = labels.indexOf(m.prediction.result);
                    const conf = m.prediction.confidence?.[resultIndex] ?? 0;
                    const predLabel =
                        m.prediction.result === 'Home Win'
                        ? `${m.home} to win`
                        : m.prediction.result === 'Away Win'
                        ? `${m.away} to win`
                        : 'Draw';

                    return (
                        <div
                        key={i}
                        className="bg-gray-400 rounded-lg shadow-md p-4 flex flex-col items-center"
                        >
                        {/* Home Crest */}
                        <img
                            src={teamLogos[m.home]}
                            alt={m.home}
                            className="w-16 h-16 mb-2"
                        />
                        <div className="text-center mb-1">
                            <p className="text-xs text-gray-600">Home</p>
                            <p className="font-medium">{m.home}</p>
                        </div>

                        {/* Score */}
                        <div className="bg-gray-300 rounded-full px-4 py-2 mb-2 border">
                            <p className="text-lg font-bold text-gray-800">
                            {m.score.home} – {m.score.away}
                            </p>
                        </div>

                        <div className="text-center mt-1">
                            <p className="text-xs text-gray-600">Away</p>
                            <p className="font-medium">{m.away}</p>
                        </div>
                        {/* Away Crest */}
                        <img
                            src={teamLogos[m.away]}
                            alt={m.away}
                            className="w-16 h-16 mt-2"
                        />

                        {/* Prediction */}
                        <div className="bg-gray-300 mt-3 rounded-full px-3 py-1 border">
                            <p className="text-[#E30613] text-sm">
                            Predicted: {predLabel} 
                            </p>
                        </div>

                        {/* Date */}
                        <p className="mt-3 text-xs text-gray-600">
                            {new Date(m.utcDate).toLocaleDateString()}
                        </p>
                        </div>
                    );
                    })}
                </div>
                ) : (
                <p className="text-gray-600 italic">No recent matches found.</p>
                )
            ) : (
                <p className="text-gray-500 italic">
                Select a team to view recent results.
                </p>
            )}
            </div>
        </div>
        </div>
    );
}
