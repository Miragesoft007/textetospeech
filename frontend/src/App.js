import { useState, useEffect, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Volume2, Download, Trash2, Clock, Mic2, Sparkles, Play, Pause, Loader2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [text, setText] = useState("");
  const [voice, setVoice] = useState("onyx");
  const [speed, setSpeed] = useState([1.0]);
  const [voices, setVoices] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [history, setHistory] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    fetchVoices();
    fetchHistory();
  }, []);

  const fetchVoices = async () => {
    try {
      const response = await axios.get(`${API}/tts/voices`);
      setVoices(response.data.voices);
    } catch (error) {
      console.error("Erreur lors du chargement des voix:", error);
      toast.error("Impossible de charger les voix disponibles");
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/tts/history`);
      setHistory(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement de l'historique:", error);
    }
  };

  const generateSpeech = async () => {
    if (!text.trim()) {
      toast.error("Veuillez entrer du texte à convertir");
      return;
    }

    setIsGenerating(true);
    const startTime = Date.now();

    try {
      const response = await axios.post(
        `${API}/tts/generate`,
        {
          text: text,
          voice: voice,
          speed: speed[0]
        },
        {
          responseType: 'blob'
        }
      );

      const duration = (Date.now() - startTime) / 1000;

      // Créer une URL pour l'audio
      const url = URL.createObjectURL(response.data);
      setAudioUrl(url);
      
      toast.success("Audio généré avec succès!");

      // Sauvegarder dans l'historique
      await axios.post(`${API}/tts/history`, {
        text: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
        voice: voice,
        speed: speed[0],
        duration: duration
      });

      fetchHistory();
    } catch (error) {
      console.error("Erreur lors de la génération:", error);
      if (error.response?.status === 429) {
        toast.error("Limite de requêtes dépassée. Veuillez réessayer plus tard.");
      } else {
        toast.error("Erreur lors de la génération de l'audio");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadAudio = () => {
    if (audioUrl) {
      const a = document.createElement('a');
      a.href = audioUrl;
      a.download = 'synthese_vocale.mp3';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      toast.success("Téléchargement lancé!");
    }
  };

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const deleteHistoryItem = async (id) => {
    try {
      await axios.delete(`${API}/tts/history/${id}`);
      toast.success("Élément supprimé");
      fetchHistory();
    } catch (error) {
      console.error("Erreur lors de la suppression:", error);
      toast.error("Erreur lors de la suppression");
    }
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('fr-FR', { 
      day: '2-digit', 
      month: 'short', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="app-container">
      <div className="content-wrapper">
        {/* Header */}
        <header className="header">
          <div className="header-content">
            <div className="logo-section">
              <div className="logo-icon">
                <Mic2 className="w-8 h-8" />
              </div>
              <div>
                <h1 className="app-title">Synthèse Vocale AI</h1>
                <p className="app-subtitle">Transformez votre texte en voix naturelle</p>
              </div>
            </div>
            <div className="sparkle-badge">
              <Sparkles className="w-4 h-4" />
              <span>Intelligence Artificielle</span>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <div className="main-content">
          {/* Generator Section */}
          <div className="generator-section">
            <Card className="generator-card" data-testid="generator-card">
              <CardHeader>
                <CardTitle className="card-title">Créer une synthèse vocale</CardTitle>
                <CardDescription>Entrez votre texte et choisissez une voix pour générer l'audio</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Text Input */}
                <div className="input-group">
                  <label className="input-label">
                    <Volume2 className="w-4 h-4" />
                    Votre texte
                  </label>
                  <Textarea
                    data-testid="text-input"
                    placeholder="Entrez le texte que vous souhaitez convertir en audio. L'IA comprendra automatiquement la ponctuation pour une intonation naturelle. Vous pouvez entrer des textes longs, ils seront automatiquement découpés et fusionnés..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    className="text-area"
                    rows={6}
                  />
                  <div className="char-counter">{text.length} / 50000 caractères (découpage automatique)</div>
                </div>

                {/* Voice Selection */}
                <div className="input-group">
                  <label className="input-label">
                    <Mic2 className="w-4 h-4" />
                    Voix
                  </label>
                  <Select value={voice} onValueChange={setVoice}>
                    <SelectTrigger data-testid="voice-select" className="select-trigger">
                      <SelectValue placeholder="Sélectionnez une voix" />
                    </SelectTrigger>
                    <SelectContent>
                      {voices.map((v) => (
                        <SelectItem key={v.id} value={v.id} data-testid={`voice-option-${v.id}`}>
                          <div className="voice-option">
                            <span className="voice-name">{v.name}</span>
                            <span className="voice-description">{v.description}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Speed Control */}
                <div className="input-group">
                  <label className="input-label">
                    <Clock className="w-4 h-4" />
                    Vitesse: {speed[0]}x
                  </label>
                  <Slider
                    data-testid="speed-slider"
                    value={speed}
                    onValueChange={setSpeed}
                    min={0.25}
                    max={4}
                    step={0.25}
                    className="slider"
                  />
                  <div className="speed-labels">
                    <span>0.25x</span>
                    <span>1x</span>
                    <span>4x</span>
                  </div>
                </div>

                {/* Generate Button */}
                <Button
                  data-testid="generate-button"
                  onClick={generateSpeech}
                  disabled={isGenerating || !text.trim()}
                  className="generate-button"
                  size="lg"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Génération en cours...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      Générer l'audio
                    </>
                  )}
                </Button>

                {/* Audio Player */}
                {audioUrl && (
                  <div className="audio-player" data-testid="audio-player">
                    <div className="audio-controls">
                      <Button
                        data-testid="play-pause-button"
                        onClick={togglePlayPause}
                        variant="outline"
                        size="icon"
                        className="play-button"
                      >
                        {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                      </Button>
                      <audio
                        ref={audioRef}
                        src={audioUrl}
                        onEnded={() => setIsPlaying(false)}
                        onPlay={() => setIsPlaying(true)}
                        onPause={() => setIsPlaying(false)}
                        className="audio-element"
                      />
                      <div className="audio-info">
                        <span className="audio-status">{isPlaying ? "En lecture..." : "Prêt à écouter"}</span>
                      </div>
                      <Button
                        data-testid="download-button"
                        onClick={downloadAudio}
                        variant="outline"
                        size="icon"
                        className="download-button"
                      >
                        <Download className="w-5 h-5" />
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* History Section */}
          <div className="history-section">
            <Card className="history-card" data-testid="history-card">
              <CardHeader>
                <CardTitle className="card-title">Historique</CardTitle>
                <CardDescription>Vos conversions récentes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="history-list">
                  {history.length === 0 ? (
                    <div className="empty-state">
                      <Volume2 className="w-12 h-12 opacity-20" />
                      <p>Aucune conversion pour le moment</p>
                    </div>
                  ) : (
                    history.map((item) => (
                      <div key={item.id} className="history-item" data-testid={`history-item-${item.id}`}>
                        <div className="history-content">
                          <p className="history-text">{item.text}</p>
                          <div className="history-meta">
                            <span className="history-voice">{item.voice}</span>
                            <span className="history-speed">{item.speed}x</span>
                            <span className="history-date">{formatDate(item.timestamp)}</span>
                          </div>
                        </div>
                        <Button
                          data-testid={`delete-history-${item.id}`}
                          onClick={() => deleteHistoryItem(item.id)}
                          variant="ghost"
                          size="icon"
                          className="delete-button"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;