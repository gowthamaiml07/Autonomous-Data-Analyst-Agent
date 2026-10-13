"""Scikit-learn and time-series predictive modeling engine with live What-If simulation and multi-scenario forecasting."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from src.config import PLOTLY_COLORWAY


@dataclass
class PredictionResult:
    """Comprehensive output of predictive modeling or time-series forecast."""
    success: bool
    task_type: str  # 'regression', 'classification', 'forecast'
    target_column: str
    model_name: str
    metrics: Dict[str, float] = field(default_factory=dict)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    test_comparison_table: Optional[pd.DataFrame] = None
    comparison_chart: Optional[go.Figure] = None
    forecast_table: Optional[pd.DataFrame] = None
    forecast_chart: Optional[go.Figure] = None
    executive_summary: str = ""
    limitations: List[str] = field(default_factory=list)
    trained_pipeline: Optional[Any] = None
    features_used: List[str] = field(default_factory=list)
    default_feature_values: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class DataPredictor:
    """Executes robust, leakage-free predictive analytics, forecasting, and interactive What-If simulation."""

    @classmethod
    def train_regression(
        cls,
        df: pd.DataFrame,
        target_col: str,
        feature_cols: Optional[List[str]] = None,
        model_type: str = "random_forest",
        test_size: float = 0.20
    ) -> PredictionResult:
        """Fit regression model with strict train/test split and leakage-free pipeline."""
        if target_col not in df.columns:
            return PredictionResult(success=False, task_type="regression", target_column=target_col, model_name=model_type, error=f"Target '{target_col}' not found.")

        valid_df = df.dropna(subset=[target_col]).copy()
        valid_df[target_col] = pd.to_numeric(valid_df[target_col], errors="coerce")
        valid_df = valid_df.dropna(subset=[target_col])

        if len(valid_df) < 20:
            return PredictionResult(
                success=False, task_type="regression", target_column=target_col, model_name=model_type,
                error="Dataset too small for reliable regression (< 20 valid rows)."
            )

        if not feature_cols:
            feature_cols = [c for c in valid_df.columns if c != target_col]
        usable_features = []
        for c in feature_cols:
            if c != target_col and valid_df[c].nunique() > 1 and valid_df[c].nunique() < len(valid_df) * 0.95:
                usable_features.append(c)

        if not usable_features:
            return PredictionResult(
                success=False, task_type="regression", target_column=target_col, model_name=model_type,
                error="No valid predictive features identified after excluding IDs and constants."
            )

        X = valid_df[usable_features]
        y = valid_df[target_col]

        num_features = X.select_dtypes(include=[np.number]).columns.tolist()
        cat_features = [c for c in usable_features if c not in num_features]

        transformers = []
        if num_features:
            transformers.append(("num", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ]), num_features))
        if cat_features:
            transformers.append(("cat", Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
                ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
            ]), cat_features))

        preprocessor = ColumnTransformer(transformers=transformers)

        if model_type == "linear":
            model = LinearRegression()
            m_label = "Linear Regression"
        elif model_type == "gradient_boosting":
            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            m_label = "Gradient Boosting Regressor"
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            m_label = "Random Forest Regressor"

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", model)
        ])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        try:
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)
        except Exception as e:
            return PredictionResult(
                success=False, task_type="regression", target_column=target_col, model_name=m_label,
                error=f"Model training failed: {str(e)}"
            )

        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(root_mean_squared_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        comp_df = pd.DataFrame({
            "Actual": y_test.values,
            "Predicted": np.round(y_pred, 2),
            "Residual": np.round(y_test.values - y_pred, 2)
        }).head(50)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(comp_df))),
            y=comp_df["Actual"],
            mode="lines+markers",
            name="Actual",
            line=dict(color="#3B82F6", width=2)
        ))
        fig.add_trace(go.Scatter(
            x=list(range(len(comp_df))),
            y=comp_df["Predicted"],
            mode="lines+markers",
            name="Predicted",
            line=dict(color="#2563EB", width=2, dash="dash")
        ))
        fig.update_layout(
            title=f"Actual vs. Predicted {target_col} (Holdout Test Set)",
            xaxis_title="Sample Index",
            yaxis_title=target_col,
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(family="Inter, sans-serif")
        )

        feat_importance = {}
        fitted_model = pipeline.named_steps["model"]
        if hasattr(fitted_model, "feature_importances_"):
            try:
                fitted_prep = pipeline.named_steps["preprocessor"]
                feat_names = fitted_prep.get_feature_names_out()
                importances = fitted_model.feature_importances_
                top_indices = np.argsort(importances)[::-1][:10]
                for idx in top_indices:
                    name_clean = feat_names[idx].replace("num__", "").replace("cat__", "")
                    feat_importance[name_clean] = round(float(importances[idx]), 4)
            except Exception:
                pass

        # Calculate default feature values for live What-If simulation
        defaults = {}
        for col in usable_features:
            if col in num_features:
                defaults[col] = float(valid_df[col].median())
            else:
                defaults[col] = str(valid_df[col].mode()[0]) if len(valid_df[col].mode()) > 0 else "Default"

        summary = (
            f"Trained **{m_label}** to predict `{target_col}` across {len(usable_features)} features. "
            f"Evaluated on a **{int(test_size*100)}% holdout test set** ({len(X_test)} samples). "
            f"Achieved **R² = {r2:.3f}**, **MAE = {mae:,.2f}**, and **RMSE = {rmse:,.2f}**."
        )

        limitations = [
            f"Evaluated on historical sample of {len(valid_df)} rows; predictions reflect historical patterns.",
            f"Estimated prediction error variance is RMSE = {rmse:,.2f}.",
            "Linear and tree models assume stationary relationships across features."
        ]

        return PredictionResult(
            success=True,
            task_type="regression",
            target_column=target_col,
            model_name=m_label,
            metrics={"MAE": round(mae, 3), "RMSE": round(rmse, 3), "R2": round(r2, 3)},
            feature_importance=feat_importance,
            test_comparison_table=comp_df,
            comparison_chart=fig,
            executive_summary=summary,
            limitations=limitations,
            trained_pipeline=pipeline,
            features_used=usable_features,
            default_feature_values=defaults
        )

    @classmethod
    def train_classification(
        cls,
        df: pd.DataFrame,
        target_col: str,
        feature_cols: Optional[List[str]] = None,
        model_type: str = "random_forest",
        test_size: float = 0.20
    ) -> PredictionResult:
        """Fit classification model with evaluation metrics and confusion matrix."""
        if target_col not in df.columns:
            return PredictionResult(success=False, task_type="classification", target_column=target_col, model_name=model_type, error=f"Target '{target_col}' not found.")

        valid_df = df.dropna(subset=[target_col]).copy()
        if len(valid_df) < 20:
            return PredictionResult(
                success=False, task_type="classification", target_column=target_col, model_name=model_type,
                error="Dataset too small for classification (< 20 rows)."
            )

        n_classes = valid_df[target_col].nunique()
        if n_classes < 2:
            return PredictionResult(
                success=False, task_type="classification", target_column=target_col, model_name=model_type,
                error=f"Target column '{target_col}' only has 1 unique class."
            )

        if not feature_cols:
            feature_cols = [c for c in valid_df.columns if c != target_col]
        usable_features = []
        for c in feature_cols:
            if c != target_col and valid_df[c].nunique() > 1 and valid_df[c].nunique() < len(valid_df) * 0.95:
                usable_features.append(c)

        if not usable_features:
            return PredictionResult(
                success=False, task_type="classification", target_column=target_col, model_name=model_type,
                error="No valid predictive features identified for classification."
            )

        X = valid_df[usable_features]
        y = valid_df[target_col].astype(str)

        num_features = X.select_dtypes(include=[np.number]).columns.tolist()
        cat_features = [c for c in usable_features if c not in num_features]

        transformers = []
        if num_features:
            transformers.append(("num", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ]), num_features))
        if cat_features:
            transformers.append(("cat", Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
                ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
            ]), cat_features))

        preprocessor = ColumnTransformer(transformers=transformers)

        if model_type == "logistic":
            model = LogisticRegression(max_iter=1000, random_state=42)
            m_label = "Logistic Regression"
        elif model_type == "gradient_boosting":
            model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            m_label = "Gradient Boosting Classifier"
        else:
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            m_label = "Random Forest Classifier"

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", model)
        ])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if n_classes <= 5 else None
        )

        try:
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)
        except Exception as e:
            return PredictionResult(
                success=False, task_type="classification", target_column=target_col, model_name=m_label,
                error=f"Model training failed: {str(e)}"
            )

        acc = float(accuracy_score(y_test, y_pred))
        avg_mode = "binary" if n_classes == 2 else "weighted"
        pos_label = y_test.unique()[0] if n_classes == 2 else None
        
        try:
            prec = float(precision_score(y_test, y_pred, average=avg_mode, pos_label=pos_label, zero_division=0))
            rec = float(recall_score(y_test, y_pred, average=avg_mode, pos_label=pos_label, zero_division=0))
            f1 = float(f1_score(y_test, y_pred, average=avg_mode, pos_label=pos_label, zero_division=0))
        except Exception:
            prec, rec, f1 = acc, acc, acc

        labels = sorted(list(set(y_test) | set(y_pred)))
        cm = confusion_matrix(y_test, y_pred, labels=labels)
        cm_fig = px.imshow(
            cm,
            x=labels,
            y=labels,
            labels=dict(x="Predicted Class", y="Actual Class"),
            text_auto=True,
            title=f"Confusion Matrix ({m_label})",
            color_continuous_scale=[[0, "#E2E8F0"], [1, "#2563EB"]]
        )
        cm_fig.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC")

        comp_df = pd.DataFrame({
            "Actual": y_test.values,
            "Predicted": y_pred,
            "Match": y_test.values == y_pred
        }).head(50)

        feat_importance = {}
        fitted_model = pipeline.named_steps["model"]
        if hasattr(fitted_model, "feature_importances_"):
            try:
                fitted_prep = pipeline.named_steps["preprocessor"]
                feat_names = fitted_prep.get_feature_names_out()
                importances = fitted_model.feature_importances_
                top_indices = np.argsort(importances)[::-1][:10]
                for idx in top_indices:
                    name_clean = feat_names[idx].replace("num__", "").replace("cat__", "")
                    feat_importance[name_clean] = round(float(importances[idx]), 4)
            except Exception:
                pass

        defaults = {}
        for col in usable_features:
            if col in num_features:
                defaults[col] = float(valid_df[col].median())
            else:
                defaults[col] = str(valid_df[col].mode()[0]) if len(valid_df[col].mode()) > 0 else "Default"

        summary = (
            f"Trained **{m_label}** to classify `{target_col}` ({n_classes} classes). "
            f"Achieved **Accuracy: {acc*100:.1f}%**, **Precision: {prec*100:.1f}%**, "
            f"**Recall: {rec*100:.1f}%**, and **F1-Score: {f1*100:.1f}%** on holdout test set."
        )

        limitations = [
            f"Class balance affects classification confidence. Dataset contains {n_classes} target categories.",
            "Predictions reflect patterns in historical training instances; anomalies outside training distribution may misclassify."
        ]

        return PredictionResult(
            success=True,
            task_type="classification",
            target_column=target_col,
            model_name=m_label,
            metrics={"Accuracy": round(acc, 4), "Precision": round(prec, 4), "Recall": round(rec, 4), "F1": round(f1, 4)},
            feature_importance=feat_importance,
            test_comparison_table=comp_df,
            comparison_chart=cm_fig,
            executive_summary=summary,
            limitations=limitations,
            trained_pipeline=pipeline,
            features_used=usable_features,
            default_feature_values=defaults
        )

    @classmethod
    def predict_what_if(
        cls,
        pipeline: Any,
        feature_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform real-time What-If scenario prediction from interactive feature slider values."""
        input_df = pd.DataFrame([feature_values])
        try:
            pred = pipeline.predict(input_df)[0]
            probs = {}
            if hasattr(pipeline, "predict_proba"):
                try:
                    prob_array = pipeline.predict_proba(input_df)[0]
                    classes = pipeline.classes_
                    probs = {str(c): round(float(p) * 100, 1) for c, p in zip(classes, prob_array)}
                except Exception:
                    pass

            return {
                "success": True,
                "prediction": round(float(pred), 2) if isinstance(pred, (int, float, np.number)) else str(pred),
                "probabilities": probs
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def forecast_timeseries(
        cls,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        horizon_periods: int = 30,
        confidence_level: float = 0.95,
        freq: str = "D"
    ) -> PredictionResult:
        """Autoregressive and trend-based time-series forecasting with customizable confidence intervals and scenarios."""
        if date_col not in df.columns or value_col not in df.columns:
            return PredictionResult(
                success=False, task_type="forecast", target_column=value_col, model_name="Time Series",
                error=f"Columns '{date_col}' or '{value_col}' not found."
            )

        df_work = df[[date_col, value_col]].copy()
        df_work[date_col] = pd.to_datetime(df_work[date_col], errors="coerce")
        df_work[value_col] = pd.to_numeric(df_work[value_col], errors="coerce")
        df_work = df_work.dropna().sort_values(date_col)

        if len(df_work) < 15:
            return PredictionResult(
                success=False, task_type="forecast", target_column=value_col, model_name="Time Series",
                error="Insufficient time-series data (< 15 historical points)."
            )

        df_work.set_index(date_col, inplace=True)
        try:
            ts = df_work[value_col].resample(freq).sum().reset_index()
        except Exception:
            ts = df_work[value_col].resample("D").sum().reset_index()

        ts = ts.dropna()
        if len(ts) < 10:
            return PredictionResult(
                success=False, task_type="forecast", target_column=value_col, model_name="Time Series",
                error="Resampled time series contains too few intervals for trend fitting."
            )

        split_idx = int(len(ts) * 0.8)
        ts["Time_Index"] = np.arange(len(ts))
        ts["Lag_1"] = ts[value_col].shift(1).bfill()
        ts["Lag_2"] = ts[value_col].shift(2).bfill()
        ts["Rolling_Mean"] = ts[value_col].shift(1).rolling(3, min_periods=1).mean().bfill()

        train_ts = ts.iloc[:split_idx]
        test_ts = ts.iloc[split_idx:]

        features = ["Time_Index", "Lag_1", "Lag_2", "Rolling_Mean"]
        model = LinearRegression()
        model.fit(train_ts[features], train_ts[value_col])

        test_preds = model.predict(test_ts[features])
        test_mae = float(mean_absolute_error(test_ts[value_col], test_preds))
        test_rmse = float(root_mean_squared_error(test_ts[value_col], test_preds))

        model_full = LinearRegression()
        model_full.fit(ts[features], ts[value_col])

        last_date = ts[date_col].max()
        future_dates = pd.date_range(start=last_date, periods=horizon_periods + 1, freq=freq)[1:]

        future_records = []
        curr_l1 = float(ts[value_col].iloc[-1])
        curr_l2 = float(ts[value_col].iloc[-2]) if len(ts) > 1 else curr_l1
        rolling_vals = [curr_l2, curr_l1]

        noise_std = float(test_rmse) if test_rmse > 0 else float(ts[value_col].std() * 0.1)
        z_multiplier = 1.96 if confidence_level >= 0.95 else (1.645 if confidence_level >= 0.90 else 1.28)

        for i, f_date in enumerate(future_dates):
            t_idx = len(ts) + i
            r_mean = float(np.mean(rolling_vals[-3:]))
            feat_vec = pd.DataFrame([{
                "Time_Index": t_idx,
                "Lag_1": curr_l1,
                "Lag_2": curr_l2,
                "Rolling_Mean": r_mean
            }])
            pred_val = float(model_full.predict(feat_vec)[0])
            pred_val = max(0.0, pred_val)

            uncertainty = noise_std * (1 + 0.05 * i)
            upper_bound = pred_val + z_multiplier * uncertainty
            lower_bound = max(0.0, pred_val - z_multiplier * uncertainty)

            # Scenario trajectories
            optimistic = round(pred_val * 1.15, 2)
            conservative = round(max(0.0, pred_val * 0.90), 2)

            future_records.append({
                date_col: f_date.strftime("%Y-%m-%d"),
                "Forecasted": round(pred_val, 2),
                "Baseline_Forecast": round(pred_val, 2),
                "Optimistic_Scenario": optimistic,
                "Conservative_Scenario": conservative,
                f"Lower_Bound_{int(confidence_level*100)}%": round(lower_bound, 2),
                f"Upper_Bound_{int(confidence_level*100)}%": round(upper_bound, 2)
            })

            curr_l2 = curr_l1
            curr_l1 = pred_val
            rolling_vals.append(pred_val)

        forecast_df = pd.DataFrame(future_records)

        # Plotly Multi-Scenario Forecast Figure
        fig = go.Figure()
        # Historical
        fig.add_trace(go.Scatter(
            x=ts[date_col].dt.strftime("%Y-%m-%d"),
            y=ts[value_col],
            mode="lines",
            name="Historical Observed",
            line=dict(color="#111827", width=2)
        ))
        # Upper Bound
        up_col = f"Upper_Bound_{int(confidence_level*100)}%"
        low_col = f"Lower_Bound_{int(confidence_level*100)}%"
        fig.add_trace(go.Scatter(
            x=forecast_df[date_col],
            y=forecast_df[up_col],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        ))
        fig.add_trace(go.Scatter(
            x=forecast_df[date_col],
            y=forecast_df[low_col],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(37, 99, 235, 0.15)",
            name=f"{int(confidence_level*100)}% Confidence Interval"
        ))
        # Baseline
        fig.add_trace(go.Scatter(
            x=forecast_df[date_col],
            y=forecast_df["Baseline_Forecast"],
            mode="lines+markers",
            name="Baseline Forecast",
            line=dict(color="#2563EB", width=3, dash="dot")
        ))
        # Optimistic
        fig.add_trace(go.Scatter(
            x=forecast_df[date_col],
            y=forecast_df["Optimistic_Scenario"],
            mode="lines",
            name="Optimistic (+15%)",
            line=dict(color="#3B82F6", width=2, dash="dash")
        ))
        # Conservative
        fig.add_trace(go.Scatter(
            x=forecast_df[date_col],
            y=forecast_df["Conservative_Scenario"],
            mode="lines",
            name="Conservative (-10%)",
            line=dict(color="#D97706", width=2, dash="dash")
        ))

        fig.update_layout(
            title=f"Multi-Scenario Time-Series Forecast: {value_col} ({horizon_periods} Periods)",
            xaxis_title=date_col,
            yaxis_title=value_col,
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(family="Inter, sans-serif")
        )

        avg_future = float(forecast_df["Baseline_Forecast"].mean())
        summary = (
            f"Generated **{horizon_periods}-period multi-scenario forecast** for `{value_col}`. "
            f"Holdout backtest validation achieved **MAE = {test_mae:,.2f}** and **RMSE = {test_rmse:,.2f}**. "
            f"Baseline projected mean is **{avg_future:,.2f}**, with optimistic (+15%) and conservative (-10%) scenarios."
        )

        limitations = [
            "Time-series models assume continuation of historical seasonality and macroeconomic factors.",
            f"Confidence interval bands expand as the forecast horizon increases into the future.",
            "Unexpected exogenous shocks (policy changes, supply chain disruptions) are not modeled."
        ]

        return PredictionResult(
            success=True,
            task_type="forecast",
            target_column=value_col,
            model_name="Autoregressive Multi-Scenario Model",
            metrics={"Validation_MAE": round(test_mae, 2), "Validation_RMSE": round(test_rmse, 2)},
            forecast_table=forecast_df,
            forecast_chart=fig,
            executive_summary=summary,
            limitations=limitations
        )
