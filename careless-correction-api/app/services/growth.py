from app.config import Settings

settings = Settings()


def generate_assessment_prompt(
    mistake_count: int,
    completion_rate: int,
    item_loss_count: int,
    habit_title: str,
) -> str:
    return (
        f'基于以下孩子的成长数据，生成阶段性评估报告：\n'
        f'- 错题总数：{mistake_count}\n'
        f'- 任务完成率：{completion_rate}%\n'
        f'- 物品丢失次数：{item_loss_count}\n'
        f'- 当前习惯：{habit_title}\n'
        f'要求指出进步方面、需要关注的方面、以及给家长的具体建议。\n'
        f'返回 JSON 格式：{{ "progress": "...", "concerns": "...", "suggestions": "..." }}'
    )
