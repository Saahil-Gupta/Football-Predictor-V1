import React from "react";
import { Link } from "react-router-dom";
import eplLogo from "../assets/EplLogo.png";
import laligaLogo from "../assets/LaLigaLogo.png";
import Header from "../components/Header.jsx";

export default function Home() {
    return (
        <div>   
            <Header />
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center p-6">
        <h1 className="text-5xl font-extrabold text-gray-800 mb-12 text-center">
            ⚽ Choose Your League
        </h1>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-10 w-full max-w-4xl">
            {/* EPL Card */}
            <Link
            to="/epl"
            className="bg-violet-200 rounded-2xl shadow-lg p-8 flex flex-col items-center border-t-4 border-violet-600 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300"
            >
            <img src={eplLogo} alt="EPL Logo" className="w-24 h-24 mb-4 rounded-full p-2 shadow border border-gray-200" />
            <h2 className="text-3xl font-bold text-violet-700 mb-2">English Premier League</h2>
            <p className="text-gray-500 text-center">Explore upcoming fixtures, predictions, and results.</p>
            </Link>

            {/* LaLiga Card */}
            <Link
            to="/laliga"
            className="bg-red-200 rounded-2xl shadow-lg p-8 flex flex-col items-center border-t-4 border-red-600 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300"
            >
            <img src={laligaLogo} alt="LaLiga Logo" className="w-24 h-24 mb-4 rounded-full p-2 shadow" />
            <h2 className="text-3xl font-bold text-red-600 mb-2">La Liga</h2>
            <p className="text-gray-500 text-center">Dive into Spanish football predictions and stats.</p>
            </Link>
        </div>
        </div>
        </div>
    );
}
