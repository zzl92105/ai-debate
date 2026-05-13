import json
from functools import lru_cache

from app.config import get_settings
from app.schemas.debate import (
    DebateMessage,
    DebateRequest,
    DebateResponse,
    JudgeResult,
    JudgeScore,
)
from app.services.deepseek_client import DeepSeekClient

STYLE_LABELS = {
    "serious": "严肃、清晰、适合大众理解",
    "academic": "学术、重视概念定义和证据链",
    "sharp": "犀利、进攻性更强但保持理性",
    "humorous": "幽默、有表达张力但不牺牲逻辑",
}

PHASES = {
    1: "开篇陈词",
    2: "交叉反驳",
}


class DebateService:
    def __init__(self, client: DeepSeekClient):
        self.client = client

    async def run(self, request: DebateRequest) -> DebateResponse:
        topic = request.topic.strip()
        if not topic:
            raise ValueError("Topic cannot be empty")

        if not self.client.is_configured:
            return self._mock_response(request)

        messages: list[DebateMessage] = []
        transcript: list[str] = []

        for round_number in range(1, request.rounds + 1):
            phase = self._phase(round_number, request.rounds)
            affirmative = await self._generate_speech(
                topic=topic,
                style=request.style,
                role="affirmative",
                round_number=round_number,
                phase=phase,
                transcript=transcript,
            )
            messages.append(
                DebateMessage(
                    role="affirmative",
                    round=round_number,
                    phase=phase,
                    content=affirmative,
                )
            )
            transcript.append(f"正方第 {round_number} 轮：{affirmative}")

            negative = await self._generate_speech(
                topic=topic,
                style=request.style,
                role="negative",
                round_number=round_number,
                phase=phase,
                transcript=transcript,
            )
            messages.append(
                DebateMessage(
                    role="negative",
                    round=round_number,
                    phase=phase,
                    content=negative,
                )
            )
            transcript.append(f"反方第 {round_number} 轮：{negative}")

        judge = await self._judge(topic, request.style, transcript)

        return DebateResponse(
            topic=topic,
            style=request.style,
            rounds=request.rounds,
            messages=messages,
            judge=judge,
            model=self.client.model,
            mock=False,
        )

    async def _generate_speech(
        self,
        *,
        topic: str,
        style: str,
        role: str,
        round_number: int,
        phase: str,
        transcript: list[str],
    ) -> str:
        side = "正方，必须支持辩题" if role == "affirmative" else "反方，必须反对辩题"
        previous = "\n".join(transcript[-6:]) or "暂无前文。"
        prompt = f"""
辩题：{topic}
你的身份：{side}
当前阶段：第 {round_number} 轮，{phase}
表达风格：{STYLE_LABELS[style]}

已有辩论记录：
{previous}

请输出这一轮发言。要求：
1. 只输出发言正文，不要加标题。
2. 控制在 180 到 260 个中文字符。
3. 必须回应对方已有观点；如果是首轮，则建立清晰立场。
4. 不编造具体数据来源；需要事实时使用稳妥表述。
""".strip()

        return await self.client.chat(
            [
                {
                    "role": "system",
                    "content": "你是专业辩手，擅长结构化论证、抓住对方漏洞并保持表达克制。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.75,
        )

    async def _judge(self, topic: str, style: str, transcript: list[str]) -> JudgeResult:
        prompt = f"""
你是中立辩论裁判。请根据以下辩论记录评分。

辩题：{topic}
风格：{STYLE_LABELS[style]}

辩论记录：
{chr(10).join(transcript)}

请严格输出 JSON，不要 Markdown。格式：
{{
  "winner": "affirmative|negative|draw",
  "score": {{"affirmative": 0-100, "negative": 0-100}},
  "reason": "胜负理由，120字以内",
  "best_argument": "本场最佳论点，80字以内",
  "logic_flaws": ["主要逻辑漏洞1", "主要逻辑漏洞2"]
}}
""".strip()

        content = await self.client.chat(
            [
                {"role": "system", "content": "你是严格、中立、只输出合法 JSON 的辩论裁判。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        try:
            data = json.loads(content)
            return JudgeResult.model_validate(data)
        except Exception:
            return JudgeResult(
                winner="draw",
                score=JudgeScore(affirmative=75, negative=75),
                reason="裁判输出未能解析为结构化结果，因此暂定双方平局。原始评价已被省略。",
                best_argument="双方均提出了可讨论的核心观点。",
                logic_flaws=["裁判 JSON 解析失败，需要重新生成或降低输出随机性。"],
            )

    def _phase(self, round_number: int, total_rounds: int) -> str:
        if round_number == 1:
            return PHASES[1]
        if round_number == total_rounds:
            return "总结陈词"
        return PHASES[2]

    def _mock_response(self, request: DebateRequest) -> DebateResponse:
        topic = request.topic.strip()
        messages: list[DebateMessage] = []
        for round_number in range(1, request.rounds + 1):
            phase = self._phase(round_number, request.rounds)
            messages.append(
                DebateMessage(
                    role="affirmative",
                    round=round_number,
                    phase=phase,
                    content=(
                        f"围绕“{topic}”，正方认为关键不在于情绪化判断，而在于趋势是否已经形成。"
                        f"第 {round_number} 轮我们强调：只要收益持续超过迁移成本，这一方向就会继续扩大。"
                    ),
                )
            )
            messages.append(
                DebateMessage(
                    role="negative",
                    round=round_number,
                    phase=phase,
                    content=(
                        f"反方认为“{topic}”不能只看单一趋势。现实系统还有成本、边界条件和人的选择。"
                        f"第 {round_number} 轮我们指出：正方需要证明这种变化具有普遍性，而不是局部现象。"
                    ),
                )
            )

        return DebateResponse(
            topic=topic,
            style=request.style,
            rounds=request.rounds,
            messages=messages,
            judge=JudgeResult(
                winner="draw",
                score=JudgeScore(affirmative=82, negative=82),
                reason="当前为无 API Key 的模拟结果。双方都建立了基本立场，但还缺少真实模型生成的细节攻防。",
                best_argument="反方提醒需要区分局部趋势和普遍结论，能有效约束辩题范围。",
                logic_flaws=["正方对趋势强度的证明不足。", "反方对替代方案的正面论证还不充分。"],
            ),
            model=self.client.model,
            mock=True,
        )


@lru_cache
def get_debate_service() -> DebateService:
    return DebateService(DeepSeekClient(get_settings()))

