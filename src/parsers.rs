// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.

use serde_json::Value;
use anyhow::{Result, anyhow};

pub fn parser_ollama(response: &Value) -> Result<(u64, u64)> {
    let tokens_input = response["prompt_eval_count"]
        .as_u64()
        .ok_or_else(|| anyhow!("Missing or invalid prompt_eval_count"))?;
        
    let tokens_output = response["eval_count"]
        .as_u64()
        .ok_or_else(|| anyhow!("Missing or invalid eval_count"))?;
        
    Ok((tokens_input, tokens_output))
}

pub fn parser_deepseek(response: &Value) -> Result<(u64, u64)> {
    let tokens_input = response["usage"]["prompt_tokens"]
        .as_u64()
        .ok_or_else(|| anyhow!("Missing or invalid prompt_tokens"))?;
        
    let tokens_output = response["usage"]["completion_tokens"]
        .as_u64()
        .ok_or_else(|| anyhow!("Missing or invalid completion_tokens"))?;
        
    Ok((tokens_input, tokens_output))
}

pub fn parser_llamacpp(response: &Value) -> Result<(u64, u64)> {
    let tokens_input = response["tokens_evaluated"]
        .as_u64()
        .ok_or_else(|| anyhow!("Missing or invalid tokens_evaluated"))?;
        
    let tokens_output = response["tokens_predicted"]
        .as_u64()
        .ok_or_else(|| anyhow!("Missing or invalid tokens_predicted"))?;
        
    Ok((tokens_input, tokens_output))
}

pub fn parser_openai(response: &Value) -> Result<(u64, u64)> {
    //   "usage": {
    //     "prompt_tokens": 28,
    let tokens_input = response["usage"]["prompt_tokens"]
        .as_u64()
        .ok_or_else(|| anyhow!("Missing or invalid prompt_tokens"))?;

    //     "completion_tokens": 28
    let tokens_output = response["usage"]["completion_tokens"]
        .as_u64()
        .ok_or_else(|| anyhow!("Missing or invalid completion_tokens"))?;

    Ok((tokens_input, tokens_output))
}

pub fn parse(
    json_body: &Value,
    parser: &str,
) -> Result<(u64, u64)> {
    match parser {
        "ollama" => {
            let (input_tokens, output_tokens) = parser_ollama(&json_body)?;
            log::info!("OLLaMA tokens - input: {}, output: {}", input_tokens, output_tokens);
            Ok((input_tokens, output_tokens))
        }
        "deepseek" => {
            let (input_tokens, output_tokens) = parser_deepseek(&json_body)?;
            log::info!("Deepseek tokens - input: {}, output: {}", input_tokens, output_tokens);
            Ok((input_tokens, output_tokens))
        }
        "llamacpp" => {
            let (input_tokens, output_tokens) = parser_llamacpp(&json_body)?;
            log::info!("LLamaCPP tokens - input: {}, output: {}", input_tokens, output_tokens);
            Ok((input_tokens, output_tokens))
        }
        "openai" => {
            let (input_tokens, output_tokens) = parser_openai(&json_body)?;
            log::info!("OpenAI tokens - input: {}, output: {}", input_tokens, output_tokens);
            Ok((input_tokens, output_tokens))
        }
        _ => {
            Err(anyhow!("Parser not set for model"))
        }
    }
}
