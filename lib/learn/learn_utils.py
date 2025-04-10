import matplotlib.pyplot as plt

def plot_catboost_metrics(model, metric_name='RMSE'):
    """
    Отображает график метрики обучения и валидации для обученной модели CatBoost.

    :param model: Обученная модель CatBoost.
    :param metric_name: Название метрики (по умолчанию 'RMSE').
    """
    eval_results = model.get_evals_result()

    if 'learn' not in eval_results or 'validation' not in eval_results:
        print("Не найдены результаты обучения и/или валидации.")
        return

    train_metric = eval_results['learn'].get(metric_name)
    val_metric = eval_results['validation'].get(metric_name)

    if train_metric is None or val_metric is None:
        print(f"Метрика '{metric_name}' не найдена в результатах обучения.")
        print("Доступные метрики:", list(eval_results['learn'].keys()))
        return

    plt.figure(figsize=(10, 6))
    plt.plot(train_metric, label='Train')
    plt.plot(val_metric, label='Validation')
    plt.xlabel('Iteration')
    plt.ylabel(metric_name)
    plt.title(f'CatBoost {metric_name} over iterations')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
