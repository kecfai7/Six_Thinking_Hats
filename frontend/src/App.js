import React, { useState, useRef } from "react";
import { Container, Typography, TextField, Button, Box, Paper, CircularProgress, Grid, Card, CardContent } from "@mui/material";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import royalBotLogo from "./royalbot_logo.png";
import './i18n';
import { useTranslation } from 'react-i18next';

const HAT_COLORS = [
  { color: "흰색", eng: "White", desc: "정보, 사실, 데이터" },
  { color: "빨간색", eng: "Red", desc: "감정, 직관, 느낌" },
  { color: "검은색", eng: "Black", desc: "비판적 사고, 위험, 문제점" },
  { color: "노란색", eng: "Yellow", desc: "긍정적 사고, 장점, 기회" },
  { color: "초록색", eng: "Green", desc: "창의적 사고, 아이디어, 대안" },
  { color: "파란색", eng: "Blue", desc: "사고 관리, 결론, 진행방향" },
];

export default function App() {
  const { t, i18n } = useTranslation();
  // 다국어 HAT_COLORS 동적 생성
  const HAT_COLORS = t('hats', { returnObjects: true });
  const [problem, setProblem] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [answers, setAnswers] = useState(null);
  const [error, setError] = useState("");
  const [copySuccess, setCopySuccess] = useState("");
  const resultRef = useRef();

  // PDF 저장 및 이메일 첨부 전송 기능
  const handlePdfAndEmail = async () => {
    if (!answers) return;
    const now = new Date();
    const pad = n => n.toString().padStart(2, '0');
    const keyword = problem ? problem.replace(/[^\w가-힣]+/g, " ").trim().slice(0, 10) : "SixThinkingHats";
    const timestamp = `${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}`;
    const filename = `${keyword}_${timestamp}.pdf`;
    const formData = new FormData();
    formData.append('email', email);
    formData.append('problem', problem);
    formData.append('answers', JSON.stringify(answers));
    // 백엔드로 전송 (이메일 첨부)
    await fetch('http://localhost:5000/api/send_email_with_pdf', {
      method: 'POST',
      body: formData
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setAnswers(null);
    setCopySuccess("");
    try {
      const res = await axios.post('http://localhost:5000/api/solve', { problem, email });
      // hat_answers를 answers로 세팅
      setAnswers(res.data.hat_answers || res.data);
    } catch (err) {
      setError(t('error'));
    }
    setLoading(false);
  };

  // 결과 전체 복사 기능
  const handleCopy = () => {
    if (!answers) return;
    let text = HAT_COLORS.map(
      (hat) => `■ ${hat.color} 모자 (${hat.eng} Hat): ${hat.desc}\n` + (answers[hat.eng.toLowerCase()] || t('no_answer'))
    ).join("\n\n");
    navigator.clipboard.writeText(text).then(() => setCopySuccess(t('copy_success')));
  };

  return (
    <Container maxWidth="sm" sx={{ py: 5 }}>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
        <Button onClick={() => i18n.changeLanguage(i18n.language === 'en' ? 'ko' : 'en')}>
          {t('language')}
        </Button>
      </Box>
      <Paper elevation={4} sx={{ p: 4, borderRadius: 3, mt: 2 }}>
        <Typography variant="h4" align="center" fontWeight={700} gutterBottom color="#1976d2">
          {t('title')}
        </Typography>
        <Typography align="center" color="text.secondary" gutterBottom>
          {t('subtitle')}
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
          <TextField
            label={t('input_label')}
            multiline
            minRows={3}
            fullWidth
            required
            value={problem}
            onChange={e => setProblem(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            label={t('email_label')}
            type="email"
            fullWidth
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            sx={{ mb: 3 }}
          />
          <Button type="submit" variant="contained" color="primary" fullWidth size="large" disabled={loading}>
            {loading ? <CircularProgress size={24} /> : t('submit')}
          </Button>
        </Box>
        {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
        {answers && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button onClick={handleCopy} variant="outlined" color="primary" sx={{ mr: 1 }}>
              {t('copy')}
            </Button>
            <Button onClick={handlePdfAndEmail} variant="contained" color="secondary">
              {t('send_pdf')}
            </Button>
            {copySuccess && <span style={{ color: '#388e3c', marginLeft: 12, alignSelf: 'center' }}>{copySuccess}</span>}
          </Box>
        )}
        {answers && (
          <Box sx={{ mt: 5 }}>
            <div ref={resultRef} style={{ background: '#f0f4fc', borderRadius: 18, padding: 24, boxShadow: '0 2px 12px #0001' }}>
              <Grid container spacing={2}>
                {HAT_COLORS.map((hat, idx) => (
                  <Grid item xs={12} key={hat.eng}>
                    <Card
                      elevation={4}
                      sx={{
                        borderLeft: `8px solid ${
                          hat.eng && hat.eng.toLowerCase() === "white" ? "#e0e0e0"
                          : hat.eng && hat.eng.toLowerCase() === "red" ? "#ef9a9a"
                          : hat.eng && hat.eng.toLowerCase() === "black" ? "#212121"
                          : hat.eng && hat.eng.toLowerCase() === "yellow" ? "#ffd600"
                          : hat.eng && hat.eng.toLowerCase() === "green" ? "#43a047"
                          : "#1565c0"
                          }`,

                        minHeight: 200,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'flex-start',
                        bgcolor: '#fff',
                        ...(problem.includes('어린이') || problem.includes('초등') ? { bgcolor: '#ffe4fa' } :
                          problem.includes('청소년') || problem.includes('10대') ? { bgcolor: '#e4faff' } :
                          problem.includes('노인') || problem.includes('고령') ? { bgcolor: '#fdf6e3' } : {})
                      }}
                    >
                      <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                          {hat.color} 모자 ({hat.eng} Hat)
                        </Typography>
                        <Typography variant="body1" sx={{ mt: 1 }}>
                          {hat.desc}
                        </Typography>
                      {/* 필요시 answers[idx] 등도 추가 */}
                      <Typography variant="body2" sx={{ mt: 2}}>
                        <ReactMarkdown>
                          {answers && answers[hat.eng.toLowerCase()] 
                           ? answers[hat.eng.toLowerCase()] 
                          : t('no_answer')}
                        </ReactMarkdown>
                      </Typography>
                    </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </div>
          </Box>
        )}
      </Paper>
    </Container>
  );
}
