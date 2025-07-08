
// // App.jsx
// import React, { useState, useEffect } from 'react';
// import axios from 'axios';
// import TeamSelector from './components/TeamSelector.jsx';
// import Header from './components/Header.jsx';
// import Home from './components/Home.jsx';
// import teamLogos from './assets/teamLogos.js';

// const defaultMessages = [
//     "Calculating Mbappé's offsides...",
//     "Counting the number of times Lamine Yamal cut inside...",
//     "Analyzing Vinícius Jr.'s dribbles...",
//     "Tallying Rodrygo's sprints...",
//     "Measuring Pedri's touches..."
// ];

// function LoadingScreen({ progress }) {
//     const [msgIndex, setMsgIndex] = useState(0);

//     useEffect(() => {
//         const msgInterval = setInterval(() => {
//             setMsgIndex(i => (i + 1) % defaultMessages.length);
//         }, 2000);
//         return () => clearInterval(msgInterval);
//     }, []);

//     return (
//         <div className="fixed inset-0 bg-white flex flex-col items-center justify-center z-50">
//             <div className="text-2xl font-semibold text-gray-700 mb-4">
//                 Loading La Liga Data...
//             </div>
//             <div className="overflow-hidden whitespace-nowrap w-full text-center mb-6 text-gray-500">
//                 <div className="inline-block animate-marquee">
//                     {defaultMessages[msgIndex]}
//                 </div>
//             </div>
//             <div className="w-3/4 bg-gray-200 h-2 rounded-full overflow-hidden">
//                 <div
//                     className="h-2 bg-red-600 transition-all duration-100"
//                     style={{ width: `${progress}%` }}
//                 />
//             </div>
//         </div>
//     );
// }

// export default function App() {
//     const [teams, setTeams] = useState([]);
//     const [teamId, setTeamId] = useState('');
//     const [nextFixtures, setNextFixtures] = useState([]);
//     const [lastFixtures, setLastFixtures] = useState([]);
//     const [latestFixtures, setLatestFixtures] = useState([]);
//     const [latestMatchday, setLatestMatchday] = useState(null);
//     const [isLoading, setIsLoading] = useState(true);
//     const [progress, setProgress] = useState(0);

//     // Always show 6-second loader, fetch teams & latest matchday in background
//     useEffect(() => {
//         const start = Date.now();
//         const timer = setInterval(() => {
//             const elapsed = Date.now() - start;
//             setProgress(Math.min(100, (elapsed / 6000) * 100));
//         }, 100);

//         const timeout = setTimeout(() => {
//             clearInterval(timer);
//             setProgress(100);
//             setIsLoading(false);
//         }, 6000);

//         // Fetch team list
//         axios
//             .get('/api/teams')
//             .then(res => setTeams(res.data))
//             .catch(err => console.error('Error fetching teams:', err));

//         // Fetch latest matchday
//         axios
//             .get('/api/fixtures/matchday')
//             .then(res => {
//                 const { matchday, fixtures } = res.data;
//                 setLatestMatchday(matchday);
//                 setLatestFixtures(Array.isArray(fixtures) ? fixtures : []);
//             })
//             .catch(err => {
//                 console.error('Error fetching latest matchday:', err);
//                 setLatestMatchday(null);
//                 setLatestFixtures([]);
//             });

//         return () => {
//             clearInterval(timer);
//             clearTimeout(timeout);
//         };
//     }, []);

//     useEffect(() => {
//         if (!teamId) {
//             setNextFixtures([]);
//             setLastFixtures([]);
//             return;
//         }

//         axios
//             .get(`/api/fixtures/next/${teamId}`)
//             .then(res => setNextFixtures(Array.isArray(res.data) ? res.data : []))
//             .catch(() => setNextFixtures([]));

//         axios
//             .get(`/api/fixtures/last/${teamId}`)
//             .then(res => setLastFixtures(Array.isArray(res.data) ? res.data : []))
//             .catch(() => setLastFixtures([]));
//     }, [teamId]);

//     if (isLoading) {
//         return <LoadingScreen progress={progress} />;
//     }

//     return (
//         <div className="min-h-screen bg-gray-50 p-8">
//             <div className="max-w-4xl mx-auto">
//                 <h1 className="text-4xl font-extrabold text-gray-800 mb-8 text-center">
//                     ⚽ La Liga Predictor
//                 </h1>

//                 {/* ────────────────────────────────────────────────────────── */}

//                 {/* Team Selector */}
//                 <div className="bg-white rounded-2xl shadow p-8 mb-10 border-t-4 border-red-600">
//                     <TeamSelector
//                         label="Select Team"
//                         teams={teams}
//                         selectedTeam={teamId}
//                         onChange={setTeamId}
//                     />
//                 </div>

//                 {/* ───── Next 5 Fixture Predictions (Grid) ───── */}
//                 <div className="mt-6 bg-white rounded-2xl shadow border-t-4 border-red-600 p-6">
//                     <h2 className="text-2xl font-bold text-gray-800 mb-4">
//                         Next 5 Fixture Predictions
//                     </h2>

//                     {teamId ? (
//                         nextFixtures.length > 0 ? (
//                             <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
//                                 {nextFixtures.map((m, i) => {
//                                     const labels = ['Home Win', 'Draw', 'Away Win'];
//                                     const idx = labels.indexOf(m.prediction.result);
//                                     const predLabel =
//                                         m.prediction.result === 'Home Win'
//                                             ? `${m.home} to win`
//                                             : m.prediction.result === 'Away Win'
//                                             ? `${m.away} to win`
//                                             : 'Draw';

//                                     return (
//                                         <div
//                                             key={i}
//                                             className="bg-white rounded-lg shadow p-6 flex flex-col items-center"
//                                         >
//                                             {/* Home crest & label */}
//                                             <div className="flex flex-col items-center mb-2">
//                                                 <img
//                                                     src={teamLogos[m.home]}
//                                                     alt={m.home}
//                                                     className="w-16 h-16 mb-1"
//                                                 />
//                                                 <p className="text-xs text-gray-500">Home</p>
//                                                 <p className="font-medium text-gray-700">
//                                                     {m.home}
//                                                 </p>
//                                             </div>

//                                             {/* Prediction bubble */}
//                                             <div className="border border-red-600 rounded-full px-4 py-2 mb-2 whitespace-nowrap">
//                                                 <p className="text-red-600 text-sm">
//                                                     {predLabel}
//                                                 </p>
//                                             </div>

//                                             {/* Away crest & label */}
//                                             <div className="flex flex-col items-center mb-2">
//                                                 <p className="text-xs text-gray-500">Away</p>
//                                                 <p className="font-medium text-gray-700 mb-1">
//                                                     {m.away}
//                                                 </p>
//                                                 <img
//                                                     src={teamLogos[m.away]}
//                                                     alt={m.away}
//                                                     className="w-16 h-16"
//                                                 />
//                                             </div>

//                                             {/* Date */}
//                                             <p className="text-xs text-gray-500">
//                                                 {new Date(m.utcDate).toLocaleDateString()}
//                                             </p>
//                                         </div>
//                                     );
//                                 })}
//                             </div>
//                         ) : (
//                             <p className="text-gray-500 italic">
//                                 No upcoming matches scheduled.
//                             </p>
//                         )
//                     ) : (
//                         <p className="text-gray-500 italic">
//                             Select a team to view upcoming fixtures.
//                         </p>
//                     )}
//                 </div>

//                 {/* ───── Last 5 Results (Grid) ───── */}
//                 <div className="mt-6 bg-white rounded-2xl shadow p-6 border-t-4 border-red-600">
//                     <h2 className="text-2xl font-bold text-gray-800 mb-4">
//                         Last 5 Results
//                     </h2>

//                     {teamId ? (
//                         lastFixtures.length > 0 ? (
//                             <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
//                                 {lastFixtures.map((m, i) => {
//                                     const labels = ['Home Win', 'Draw', 'Away Win'];
//                                     const idx = labels.indexOf(m.prediction.result);
//                                     const predLabel =
//                                         m.prediction.result === 'Home Win'
//                                             ? `${m.home} to win`
//                                             : m.prediction.result === 'Away Win'
//                                             ? `${m.away} to win`
//                                             : 'Draw';

//                                     return (
//                                         <div
//                                             key={i}
//                                             className="bg-white rounded-lg shadow p-6 flex flex-col items-center"
//                                         >
//                                             {/* Home crest & label */}
//                                             <div className="flex flex-col items-center mb-2">
//                                                 <img
//                                                     src={teamLogos[m.home]}
//                                                     alt={m.home}
//                                                     className="w-16 h-16 mb-1"
//                                                 />
//                                                 <p className="text-xs text-gray-500">Home</p>
//                                                 <p className="font-medium text-gray-700">
//                                                     {m.home}
//                                                 </p>
//                                             </div>

//                                             {/* Score bubble */}
//                                             <div className="border border-red-600 rounded-full px-4 py-2 mb-2 whitespace-nowrap">
//                                                 <p className="text-red-600 font-bold">
//                                                     {m.score.home} – {m.score.away}
//                                                 </p>
//                                             </div>

//                                             {/* Away crest & label */}
//                                             <div className="flex flex-col items-center mb-2">
//                                                 <p className="text-xs text-gray-500">Away</p>
//                                                 <p className="font-medium text-gray-700 mb-1">
//                                                     {m.away}
//                                                 </p>
//                                                 <img
//                                                     src={teamLogos[m.away]}
//                                                     alt={m.away}
//                                                     className="w-16 h-16"
//                                                 />
//                                             </div>

//                                             {/* Prediction bubble */}
//                                             <div className="border border-red-600 rounded-full px-3 py-1 mb-2 whitespace-nowrap">
//                                                 <p className="text-red-600 text-sm">
//                                                     Predicted: {predLabel}
//                                                 </p>
//                                             </div>

//                                             {/* Date */}
//                                             <p className="text-xs text-gray-500">
//                                                 {new Date(m.utcDate).toLocaleDateString()}
//                                             </p>
//                                         </div>
//                                     );
//                                 })}
//                             </div>
//                         ) : (
//                             <p className="text-gray-500 italic">
//                                 No recent matches found.
//                             </p>
//                         )
//                     ) : (
//                         <p className="text-gray-500 italic">
//                             Select a team to view recent results.
//                         </p>
//                     )}
//                 </div>

//                 {/* ─────────────── Latest Matchday Section ─────────────── */}
//                 <div className="mt-6 bg-white rounded-2xl shadow p-6 border-t-4 border-red-600">
//                     <h2 className="text-2xl font-bold text-gray-800 mb-4">
//                         Latest Matchday {latestMatchday || ''}
//                     </h2>

//                     {latestFixtures.length > 0 ? (
//                         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
//                             {latestFixtures.map((m, i) => {
//                                 const homeName = m.homeTeam.name;
//                                 const awayName = m.awayTeam.name;
//                                 const predLabel =
//                                     m.prediction.result === 'Home Win'
//                                         ? `${homeName} to win`
//                                         : m.prediction.result === 'Away Win'
//                                         ? `${awayName} to win`
//                                         : 'Draw';
//                                 const ft = m.score?.fullTime || { home: '-', away: '-' };

//                                 return (
//                                     <div
//                                         key={i}
//                                         className="bg-white rounded-lg shadow p-6 flex flex-col items-center"
//                                     >
//                                         {/* Home crest & label */}
//                                         <div className="flex flex-col items-center mb-2">
//                                             <img
//                                                 src={teamLogos[homeName]}
//                                                 alt={homeName}
//                                                 className="w-16 h-16 mb-1"
//                                             />
//                                             <p className="text-xs text-gray-500">Home</p>
//                                             <p className="font-medium text-gray-700">
//                                                 {homeName}
//                                             </p>
//                                         </div>

//                                         {/* Score bubble */}
//                                         <div className="border border-red-600 rounded-full px-4 py-2 mb-2 whitespace-nowrap">
//                                             <p className="text-red-600 font-bold">
//                                                 {ft.home} – {ft.away}
//                                             </p>
//                                         </div>

//                                         {/* Away crest & label */}
//                                         <div className="flex flex-col items-center mb-2">
//                                             <p className="text-xs text-gray-500">Away</p>
//                                             <p className="font-medium text-gray-700 mb-1">
//                                                 {awayName}
//                                             </p>
//                                             <img
//                                                 src={teamLogos[awayName]}
//                                                 alt={awayName}
//                                                 className="w-16 h-16"
//                                             />
//                                         </div>

//                                         {/* Prediction bubble */}
//                                         <div className="border border-red-600 rounded-full px-3 py-1 mb-2 whitespace-nowrap">
//                                             <p className="text-red-600 text-sm">
//                                                 Predicted: {predLabel}
//                                             </p>
//                                         </div>

//                                         {/* Date */}
//                                         <p className="text-xs text-gray-500">
//                                             {new Date(m.utcDate).toLocaleDateString()}
//                                         </p>
//                                     </div>
//                                 );
//                             })}
//                         </div>
//                     ) : (
//                         <p className="text-gray-500 italic">
//                             No matchday data available.
//                         </p>
//                     )}
//                 </div>
//             </div>
//         </div>
//     );
// }

