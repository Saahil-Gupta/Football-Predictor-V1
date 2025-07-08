import React, { useEffect, useState } from "react";
import axios from "axios";
import TeamSelector from "./TeamSelector.jsx";
import teamLogos from "../assets/teamLogos.js"; // Make sure EPL team logos are included!

export default function EPLPrediction() {
    const [teams, setTeams] = useState([]);
    const [teamId, setTeamId] = useState("");
    const [nextFixtures, setNextFixtures] = useState([]);
    const [lastFixtures, setLastFixtures] = useState([]);
    const [latestFixtures, setLatestFixtures] = useState([]);
    const [latestMatchday, setLatestMatchday] = useState(null);

    useEffect(() => {
        axios
        .get("/api/epl/teams")
        .then((res) => setTeams(res.data))
        .catch((err) => console.error("Error fetching EPL teams:", err));

        axios
        .get("/api/epl/fixtures/matchday")
        .then((res) => {
            const { matchday, fixtures } = res.data;
            setLatestMatchday(matchday);
            setLatestFixtures(Array.isArray(fixtures) ? fixtures : []);
        })
        .catch((err) => {
            console.error("Error fetching EPL latest matchday:", err);
            setLatestFixtures([]);
        });
    }, []);

    useEffect(() => {
        if (!teamId) {
        setNextFixtures([]);
        setLastFixtures([]);
        return;
        }

        axios
        .get(`/api/epl/fixtures/next/${teamId}`)
        .then((res) => setNextFixtures(res.data || []))
        .catch(() => setNextFixtures([]));

        axios
        .get(`/api/epl/fixtures/last/${teamId}`)
        .then((res) => setLastFixtures(res.data || []))
        .catch(() => setLastFixtures([]));
    }, [teamId]);

    const renderFixtureCard = (m, isPastMatch = false) => {
        const predLabel =
        m.prediction?.result === "Home Win"
            ? `${m.home} to win`
            : m.prediction?.result === "Away Win"
            ? `${m.away} to win`
            : "Draw";

        return (
        <div key={m.id || m.utcDate} className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
            {/* Home */}
            <div className="flex flex-col items-center mb-2">
            <img src={teamLogos[m.home]} alt={m.home} className="w-16 h-16 mb-1" />
            <p className="text-xs text-gray-500">Home</p>
            <p className="font-medium text-gray-700">{m.home}</p>
            </div>

            {/* Score or Prediction */}
            <div className="border border-violet-600 rounded-full px-4 py-2 mb-2 whitespace-nowrap">
            {isPastMatch ? (
                <p className="text-violet-600 font-bold">
                {m.score.home} – {m.score.away}
                </p>
            ) : (
                <p className="text-violet-600 text-sm">{predLabel}</p>
            )}
            </div>

            {/* Away */}
            <div className="flex flex-col items-center mb-2">
            <p className="text-xs text-gray-500">Away</p>
            <p className="font-medium text-gray-700 mb-1">{m.away}</p>
            <img src={teamLogos[m.away]} alt={m.away} className="w-16 h-16" />
            </div>

            {/* Date */}
            <p className="text-xs text-gray-500">{new Date(m.utcDate).toLocaleDateString()}</p>

            {/* Prediction bubble for past match */}
            {isPastMatch && (
            <div className="border border-violet-600 rounded-full px-3 py-1 mt-2 whitespace-nowrap">
                <p className="text-violet-600 text-sm">Predicted: {predLabel}</p>
            </div>
            )}
        </div>
        );
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
            <h1 className="text-4xl font-extrabold text-gray-800 mb-8 text-center">⚽ EPL Predictor</h1>

            {/* Team Selector */}
            <div className="bg-white rounded-2xl shadow p-8 mb-10 border-t-4 border-violet-600">
            <TeamSelector
                label="Select Team"
                teams={teams}
                selectedTeam={teamId}
                onChange={setTeamId}
            />
            </div>

            {/* Next Fixtures */}
            <div className="mt-6 bg-white rounded-2xl shadow p-6 border-t-4 border-violet-600">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Next 5 Fixture Predictions</h2>
            {teamId ? (
                nextFixtures.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                    {nextFixtures.map((m) => renderFixtureCard(m))}
                </div>
                ) : (
                <p className="text-gray-500 italic">No upcoming matches scheduled.</p>
                )
            ) : (
                <p className="text-gray-500 italic">Select a team to view predictions.</p>
            )}
            </div>

            {/* Last Results */}
            <div className="mt-6 bg-white rounded-2xl shadow p-6 border-t-4 border-violet-600">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Last 5 Results</h2>
            {teamId ? (
                lastFixtures.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                    {lastFixtures.map((m) => renderFixtureCard(m, true))}
                </div>
                ) : (
                <p className="text-gray-500 italic">No recent matches found.</p>
                )
            ) : (
                <p className="text-gray-500 italic">Select a team to view results.</p>
            )}
            </div>

            {/* Latest Matchday */}
            <div className="mt-6 bg-white rounded-2xl shadow p-6 border-t-4 border-violet-600">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
                Latest Matchday {latestMatchday || ""}
            </h2>
            {latestFixtures.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                {latestFixtures.map((m) => {
                    return renderFixtureCard(
                    {
                        home: m.homeTeam.name,
                        away: m.awayTeam.name,
                        prediction: m.prediction,
                        score: m.score.fullTime || { home: "-", away: "-" },
                        utcDate: m.utcDate,
                    },
                    true
                    );
                })}
                </div>
            ) : (
                <p className="text-gray-500 italic">No matchday data available.</p>
            )}
            </div>
        </div>
        </div>
    );
}
