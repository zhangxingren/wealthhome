<template>
  <div>
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
      <el-radio-group v-model="scope" @change="loadAll" size="small">
        <el-radio-button value="mine">我的资产</el-radio-button>
        <el-radio-button value="family">家庭汇总</el-radio-button>
      </el-radio-group>
      <div style="font-size:12px; color:#86868b; display:flex; align-items:center; gap:4px;">
        <span>点击金额切换单位</span>
        <span style="display:inline-block; width:18px; height:18px; border-radius:50%; background:#f5f5f7; text-align:center; line-height:18px; font-size:10px; font-weight:700; color:var(--c-accent);">{{ label() }}</span>
      </div>
    </div>

    <!-- Family mode -->
    <template v-if="scope === 'family' && familyData.members">
      <div v-for="(m, mid) in familyData.members" :key="mid" style="margin-bottom:28px;">
        <h4 style="font-size:14px; font-weight:700; margin-bottom:10px; color:var(--c-text-secondary); letter-spacing:-0.2px;">
          {{ m.display_name || m.username }}
        </h4>
        <div class="stat-grid">
          <div class="stat-card card-info" @click="cycle">
            <div class="label">总资产</div><div class="value">{{ format(adjustedMember(mid, m).total_asset) }}</div>
          </div>
          <div v-if="adjustedMember(mid, m).total_liability > 0" class="stat-card card-danger" @click="cycle">
            <div class="label">总负债</div><div class="value">{{ format(adjustedMember(mid, m).total_liability) }}</div>
          </div>
          <div class="stat-card card-success" @click="cycle">
            <div class="label">净资产</div><div class="value">{{ format(adjustedMember(mid, m).net_worth) }}</div>
          </div>
          <!-- 资产分类卡片 -->
          <!-- 现金 -->
          <div v-if="!isFamilyHidden(mid, 'cash') && familyCardValue(m, 'cash') > 0" class="stat-card family-cat-card" @click="cycle">
            <div class="family-cat-top">
              <div class="label">现金</div>
              <div class="eye-btn" :class="{ off: isFamilyHidden(mid, 'cash') }" @click.stop="toggleFamilyHidden(mid, 'cash')" title="在汇总中隐藏/显示">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
            </div>
            <div class="value">{{ format(familyCardValue(m, 'cash')) }}</div>
          </div>
          <!-- 定期 -->
          <div v-if="!isFamilyHidden(mid, 'deposit') && familyCardValue(m, 'deposit') > 0" class="stat-card family-cat-card" @click="cycle">
            <div class="family-cat-top">
              <div class="label">定期</div>
              <div class="eye-btn" :class="{ off: isFamilyHidden(mid, 'deposit') }" @click.stop="toggleFamilyHidden(mid, 'deposit')" title="在汇总中隐藏/显示">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
            </div>
            <div class="value">{{ format(familyCardValue(m, 'deposit')) }}</div>
          </div>
          <!-- 基金 -->
          <div v-if="!isFamilyHidden(mid, 'fund') && familyCardValue(m, 'fund') > 0" class="stat-card family-cat-card" @click="cycle">
            <div class="family-cat-top">
              <div class="label">基金</div>
              <div class="eye-btn" :class="{ off: isFamilyHidden(mid, 'fund') }" @click.stop="toggleFamilyHidden(mid, 'fund')" title="在汇总中隐藏/显示">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
            </div>
            <div class="value">{{ format(familyCardValue(m, 'fund')) }}</div>
          </div>
          <!-- 股票 -->
          <div v-if="!isFamilyHidden(mid, 'stock') && familyCardValue(m, 'stock') > 0" class="stat-card family-cat-card" @click="cycle">
            <div class="family-cat-top">
              <div class="label">股票</div>
              <div class="eye-btn" :class="{ off: isFamilyHidden(mid, 'stock') }" @click.stop="toggleFamilyHidden(mid, 'stock')" title="在汇总中隐藏/显示">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
            </div>
            <div class="value">{{ format(familyCardValue(m, 'stock')) }}</div>
          </div>
          <!-- 债券 -->
          <div v-if="!isFamilyHidden(mid, 'bond') && familyCardValue(m, 'bond') > 0" class="stat-card family-cat-card" @click="cycle">
            <div class="family-cat-top">
              <div class="label">债券</div>
              <div class="eye-btn" :class="{ off: isFamilyHidden(mid, 'bond') }" @click.stop="toggleFamilyHidden(mid, 'bond')" title="在汇总中隐藏/显示">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
            </div>
            <div class="value">{{ format(familyCardValue(m, 'bond')) }}</div>
          </div>
          <!-- 贵金属 -->
          <div v-if="!isFamilyHidden(mid, 'precious_metal') && familyCardValue(m, 'precious_metal') > 0" class="stat-card family-cat-card" @click="cycle">
            <div class="family-cat-top">
              <div class="label">贵金属</div>
              <div class="eye-btn" :class="{ off: isFamilyHidden(mid, 'precious_metal') }" @click.stop="toggleFamilyHidden(mid, 'precious_metal')" title="在汇总中隐藏/显示">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
            </div>
            <div class="value">{{ format(familyCardValue(m, 'precious_metal')) }}</div>
          </div>
          <!-- 负债 -->
          <div v-if="!isFamilyHidden(mid, 'liability') && familyCardValue(m, 'liability') > 0" class="stat-card family-cat-card" @click="cycle">
            <div class="family-cat-top">
              <div class="label">负债</div>
              <div class="eye-btn" :class="{ off: isFamilyHidden(mid, 'liability') }" @click.stop="toggleFamilyHidden(mid, 'liability')" title="在汇总中隐藏/显示">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
            </div>
            <div class="value">{{ format(familyCardValue(m, 'liability')) }}</div>
          </div>
        </div>
      </div>

      <div v-if="familyData.family" class="family-total-card" @click="cycle">
        <div style="font-size:13px; font-weight:600; margin-bottom:16px; letter-spacing:.3px; text-transform:uppercase;">Family Total</div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px,1fr)); gap:16px;">
          <div><div class="label-dim" style="font-size:11px; margin-bottom:4px;">总资产</div><div class="value-dim" style="font-size:24px; font-weight:800; letter-spacing:-.5px;" v-html="formatHtml(adjustedFamilyTotal.total_asset)"></div></div>
          <div><div class="label-dim" style="font-size:11px; margin-bottom:4px;">总负债</div><div class="value-dim" style="font-size:24px; font-weight:800; letter-spacing:-.5px;">{{ format(adjustedFamilyTotal.total_liability) }}</div></div>
          <div><div class="label-dim" style="font-size:11px; margin-bottom:4px;">净资产</div><div class="value-dim" style="font-size:24px; font-weight:800; letter-spacing:-.5px;">{{ format(adjustedFamilyTotal.net_worth) }}</div></div>
        </div>
      </div>

      <!-- 家庭投资汇总卡片 -->
      <div class="invest-summary-card" v-if="familyInvestSummary.total_cost > 0">
        <div class="invest-summary-header">投资汇总</div>
        <div class="invest-summary-grid">
          <div class="invest-summary-item">
            <div class="invest-summary-label">总投资成本</div>
            <div class="invest-summary-value">{{ format(familyInvestSummary.total_cost) }}</div>
          </div>
          <div class="invest-summary-item">
            <div class="invest-summary-label">总投资市值</div>
            <div class="invest-summary-value">{{ format(familyInvestSummary.total_market_value) }}</div>
          </div>
          <div class="invest-summary-item" :class="{ profit: familyInvestSummary.total_profit >= 0, loss: familyInvestSummary.total_profit < 0 }">
            <div class="invest-summary-label">总盈亏</div>
            <div class="invest-summary-value">{{ familyInvestSummary.total_profit >= 0 ? '+' : '' }}{{ format(familyInvestSummary.total_profit) }}</div>
          </div>
          <div class="invest-summary-item" :class="{ profit: familyInvestSummary.total_profit >= 0, loss: familyInvestSummary.total_profit < 0 }">
            <div class="invest-summary-label">总盈亏率</div>
            <div class="invest-summary-value">{{ familyInvestSummary.total_profit_pct >= 0 ? '+' : '' }}{{ familyInvestSummary.total_profit_pct.toFixed(2) }}%</div>
          </div>
        </div>
      </div>

      <!-- Family hidden FAB -->
      <div v-if="familyHiddenCount > 0" class="hidden-fab" :class="{ open: showFamilyHidden }">
        <button class="hidden-fab-btn" @click="showFamilyHidden = !showFamilyHidden" :title="'已隐藏 ' + familyHiddenCount + ' 项'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>
          </svg>
          <span class="hidden-fab-badge">{{ familyHiddenCount }}</span>
        </button>
        <div v-if="showFamilyHidden" class="hidden-popover">
          <div class="hidden-popover-title">已隐藏的家庭资产</div>
          <div v-for="item in familyHiddenList" :key="item.uid" class="hidden-item" style="flex-direction:column; align-items:flex-start; gap:6px;">
            <span style="font-size:11px; color:var(--c-text-tertiary);">{{ item.name }}</span>
            <div v-for="cat in item.cats" :key="cat.key" style="display:flex; align-items:center; justify-content:space-between; width:100%;">
              <span class="hidden-item-label">{{ cat.label }}</span>
              <button class="restore-btn" @click="toggleFamilyHidden(item.mid, cat.key)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                恢复
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Family net worth trend chart -->
      <div class="page-card" style="margin-top:24px;">
        <div class="page-card-header"><h3>家庭净值变化趋势</h3></div>
        <div class="page-card-body">
          <TrendChart
            :data="familyTrendForChart"
            :color="'#E8654A'"
            :privacy="privacyMode"
            :tooltip-prefix="'家庭净值'"
            :empty-text="'暂无家庭净值快照'"
            embedded
          >
            <template #empty>
              <div class="icon">
                <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#c7c7cc" stroke-width="1.5"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>
              </div>
              <p>暂无家庭净值快照<br><span style="font-size:12px;">家庭成员各自记录净值快照后，此处自动汇总展示</span></p>
            </template>
          </TrendChart>
        </div>
      </div>
    </template>

    <!-- Personal mode — NEW DYNAMIC LAYOUT -->
    <template v-else>
      <!-- Top two fixed cards -->
      <div class="top-fixed-grid">
        <div class="stat-card glass-card card-primary" @click="cycle">
          <div class="label">净资产<el-tag size="small" style="margin-left:6px; vertical-align:middle;">{{ label() }}</el-tag></div>
          <div class="asset-value" v-html="formatPrivacy(formatHtml(adjustedSummary.net_worth))"></div>
          <div class="sub">净值 = 总资产 - 总负债</div>
          <div class="card-icon">🏠</div>
        </div>
        <div class="stat-card glass-card card-info" @click="cycle">
          <div class="label">总资产</div>
          <div class="asset-value" v-html="formatPrivacy(formatHtml(adjustedSummary.total_asset))"></div>
          <div class="sub">所有资产总和</div>
          <div class="card-icon">💰</div>
        </div>
      </div>

      <!-- Dynamic asset cards (only show if >0 and not hidden) -->
      <div class="dynamic-grid" v-if="hasAnyAsset">
        <!-- 现金 -->
        <div v-if="cardAssetValue('cash') > 0 && !isHidden('cash')" class="stat-card asset-card asset-cash" @click.stop="cycle">
          <div class="asset-card-top">
            <div class="asset-label">
              <span class="asset-icon">💵</span>
              <span>现金</span>
            </div>
            <div class="eye-btn" :class="{ off: isHidden('cash') }" @click.stop="toggleAssetVisibility('cash')" title="隐藏/显示">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
          </div>
          <div class="asset-value">{{ formatPrivacy(format(cardAssetValue('cash'))) }}</div>
          <div class="asset-sub">活期存款</div>
        </div>
        <!-- 定期 -->
        <div v-if="cardAssetValue('deposit') > 0 && !isHidden('deposit')" class="stat-card asset-card asset-deposit" @click.stop="cycle">
          <div class="asset-card-top">
            <div class="asset-label">
              <span class="asset-icon">🏦</span>
              <span>定期</span>
            </div>
            <div class="eye-btn" :class="{ off: isHidden('deposit') }" @click.stop="toggleAssetVisibility('deposit')" title="隐藏/显示">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
          </div>
          <div class="asset-value">{{ formatPrivacy(format(cardAssetValue('deposit'))) }}</div>
          <div class="asset-sub">已得利息 ¥{{ formatPrivacy(formatInterest(depositInterest)) }}</div>
        </div>
        <!-- 基金 -->
        <div v-if="cardAssetValue('fund') > 0 && !isHidden('fund')" class="stat-card asset-card asset-fund" @click.stop="cycle">
          <div class="asset-card-top">
            <div class="asset-label">
              <span class="asset-icon">📊</span>
              <span>基金</span>
            </div>
            <div class="eye-btn" :class="{ off: isHidden('fund') }" @click.stop="toggleAssetVisibility('fund')" title="隐藏/显示">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
          </div>
          <div class="asset-value">{{ formatPrivacy(format(cardAssetValue('fund'))) }}</div>
          <div class="asset-sub">市值</div>
        </div>
        <!-- 股票 -->
        <div v-if="cardAssetValue('stock') > 0 && !isHidden('stock')" class="stat-card asset-card asset-stock" @click.stop="cycle">
          <div class="asset-card-top">
            <div class="asset-label">
              <span class="asset-icon">📈</span>
              <span>股票</span>
            </div>
            <div class="eye-btn" :class="{ off: isHidden('stock') }" @click.stop="toggleAssetVisibility('stock')" title="隐藏/显示">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
          </div>
          <div class="asset-value">{{ formatPrivacy(format(cardAssetValue('stock'))) }}</div>
          <div class="asset-sub">持仓市值</div>
        </div>
        <!-- 债券 -->
        <div v-if="cardAssetValue('bond') > 0 && !isHidden('bond')" class="stat-card asset-card asset-bond" @click.stop="cycle">
          <div class="asset-card-top">
            <div class="asset-label">
              <span class="asset-icon">📜</span>
              <span>债券</span>
            </div>
            <div class="eye-btn" :class="{ off: isHidden('bond') }" @click.stop="toggleAssetVisibility('bond')" title="隐藏/显示">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
          </div>
          <div class="asset-value">{{ formatPrivacy(format(cardAssetValue('bond'))) }}</div>
          <div class="asset-sub">债权</div>
        </div>
        <!-- 贵金属 -->
        <div v-if="cardAssetValue('precious_metal') > 0 && !isHidden('precious_metal')" class="stat-card asset-card asset-precious-metal" @click.stop="cycle">
          <div class="asset-card-top">
            <div class="asset-label">
              <span class="asset-icon">🪙</span>
              <span>贵金属</span>
            </div>
            <div class="eye-btn" :class="{ off: isHidden('precious_metal') }" @click.stop="toggleAssetVisibility('precious_metal')" title="隐藏/显示">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
          </div>
          <div class="asset-value">{{ formatPrivacy(format(cardAssetValue('precious_metal'))) }}</div>
          <div class="asset-sub">黄金/白银等</div>
        </div>
        <!-- 负债 -->
        <div v-if="cardAssetValue('liability') > 0 && !isHidden('liability')" class="stat-card asset-card asset-liability" @click.stop="cycle">
          <div class="asset-card-top">
            <div class="asset-label">
              <span class="asset-icon">🏠</span>
              <span>负债</span>
            </div>
            <div class="eye-btn" :class="{ off: isHidden('liability') }" @click.stop="toggleAssetVisibility('liability')" title="隐藏/显示">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
          </div>
          <div class="asset-value">{{ formatPrivacy(format(cardAssetValue('liability'))) }}</div>
          <div class="asset-sub">总负债</div>
        </div>
      </div>

      <!-- Empty prompt if no assets yet -->
      <div v-if="!hasAnyAsset && !hiddenAssetList.length" class="empty-assets">
        <div class="empty-icon">📊</div>
        <h4>暂无资产记录</h4>
        <p>点击左侧菜单添加现金、定期、基金、股票、债券或贵金属，它们会动态出现在这里。</p>
      </div>

      <!-- 投资汇总卡片 -->
      <div class="invest-summary-card" v-if="investSummary.total_cost > 0">
        <div class="invest-summary-header">投资汇总</div>
        <div class="invest-summary-grid">
          <div class="invest-summary-item">
            <div class="invest-summary-label">总成本</div>
            <div class="invest-summary-value">{{ format(investSummary.total_cost) }}</div>
          </div>
          <div class="invest-summary-item">
            <div class="invest-summary-label">总市值</div>
            <div class="invest-summary-value">{{ format(investSummary.total_market_value) }}</div>
          </div>
          <div class="invest-summary-item" :class="{ profit: investSummary.total_profit >= 0, loss: investSummary.total_profit < 0 }">
            <div class="invest-summary-label">总盈亏</div>
            <div class="invest-summary-value">{{ investSummary.total_profit >= 0 ? '+' : '' }}{{ format(investSummary.total_profit) }}</div>
          </div>
          <div class="invest-summary-item" :class="{ profit: investSummary.total_profit >= 0, loss: investSummary.total_profit < 0 }">
            <div class="invest-summary-label">盈亏率</div>
            <div class="invest-summary-value">{{ investSummary.total_profit_pct >= 0 ? '+' : '' }}{{ investSummary.total_profit_pct.toFixed(2) }}%</div>
          </div>
        </div>
      </div>

      <!-- Floating hidden assets button -->
      <div v-if="hiddenAssetList.length" class="hidden-fab" :class="{ open: showHidden }">
        <button class="hidden-fab-btn" @click="showHidden = !showHidden" :title="'已隐藏 ' + hiddenAssetList.length + ' 项'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>
          </svg>
          <span class="hidden-fab-badge">{{ hiddenAssetList.length }}</span>
        </button>
        <div v-if="showHidden" class="hidden-popover">
          <div class="hidden-popover-title">已隐藏的资产</div>
          <div v-for="item in hiddenAssetList" :key="item.key" class="hidden-item">
            <span class="hidden-item-label">{{ item.label }}</span>
            <button class="restore-btn" @click="toggleAssetVisibility(item.key)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              恢复
            </button>
          </div>
        </div>
      </div>

      <!-- Net worth chart -->
      <div class="page-card" style="margin-top:24px;">
        <div class="page-card-header"><h3>净值变化趋势</h3></div>
        <div class="page-card-body">
          <TrendChart
            :data="displayTrendData"
            :color="'#6250EE'"
            :privacy="privacyMode"
            empty-text="暂无净值快照"
            embedded
          >
            <template #empty>
              <div class="icon">
                <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#c7c7cc" stroke-width="1.5"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>
              </div>
              <p>暂无净值快照<br><span style="font-size:12px;">添加资产后点击「净值趋势」页面记录</span></p>
            </template>
          </TrendChart>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch, computed } from 'vue'
import { getSummary, getTrend, getDetail, getDepositInterest, getFamilyTrend, getInvestmentSummary, getFamilyInvestmentSummary } from '../api'
import { useAmountFormat, formatHtml } from '../composables/useAmountFormat'
import { usePrivacy } from '../composables/usePrivacy'
import TrendChart from '../components/TrendChart.vue'

const scope = ref('mine')
const summary = reactive({ net_worth: 0, total_asset: 0, total_liability: 0, cash: 0, deposit: 0, fund: 0, stock: 0, bond: 0, precious_metal: 0 })
const familyData = reactive({ members: null, family: null })
const trendData = ref([])
const depositInterest = ref(0)
const showHidden = ref(false)



const investSummary = reactive({ total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
const familyInvestSummary = reactive({ total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })

const familyTrendData = ref({})

// 将 family trend {dates:[], values:[]} 转为 TrendChart 所需格式 [{snap_date, net_worth}]
const familyTrendForChart = computed(() => {
  // 显式依赖 familyHiddenAssets 以触发重算
  const _ = familyHiddenAssets.value
  const d = familyTrendData.value
  if (!d.dates || !d.values) return []
  return d.dates.map((date, i) => ({ snap_date: date, net_worth: d.values[i] || 0 }))
})

const { cycle, format, label } = useAmountFormat()
const { privacyMode, toggleAssetVisibility, isHidden, formatPrivacy, hiddenAssets, familyHiddenAssets, isFamilyHidden, toggleFamilyHidden, getFamilyHidden } = usePrivacy()

// 计算扣除隐藏资产后的调整值（个人模式）
const adjustedSummary = computed(() => {
  const s = { ...summary }
  let hiddenTotal = 0
  if (isHidden('cash')) hiddenTotal += (s.cash || 0)
  if (isHidden('deposit')) hiddenTotal += (s.deposit || 0)
  if (isHidden('fund')) hiddenTotal += (s.fund || 0)
  if (isHidden('stock')) hiddenTotal += (s.stock || 0)
  if (isHidden('bond')) hiddenTotal += (s.bond || 0)
  if (isHidden('precious_metal')) hiddenTotal += (s.precious_metal || 0)
  s.total_asset = (s.total_asset || 0) - hiddenTotal
  // 负债独立处理：隐藏时将负债归零，不从 total_asset 中扣除
  const adjustedLiability = isHidden('liability') ? 0 : (s.total_liability || 0)
  s.net_worth = s.total_asset - adjustedLiability
  return s
})

// 隐藏资产列表（用于恢复入口）
const hiddenAssetList = computed(() => {
  const map = { cash: '现金', deposit: '定期', fund: '基金', stock: '股票', bond: '债券', precious_metal: '贵金属', liability: '负债' }
  return hiddenAssets.value.map(k => ({ key: k, label: map[k] || k }))
})

// ── 家庭模式：按成员调整汇总 ──
const CAT_LABEL_MAP = { cash: '现金', deposit: '定期', fund: '基金', stock: '股票', bond: '债券', precious_metal: '贵金属', liability: '负债' }
const CAT_KEYS = ['cash', 'deposit', 'fund', 'stock', 'bond', 'precious_metal']

// ── 资产卡片配置（v-for 驱动，替代 14 个重复 div） ──
const personalAssetCardConfigs = [
  { key: 'cash', icon: '💵', label: '现金', css: 'asset-cash', sub: '活期存款' },
  { key: 'deposit', icon: '🏦', label: '定期', css: 'asset-deposit', sub: null },
  { key: 'fund', icon: '📊', label: '基金', css: 'asset-fund', sub: '市值' },
  { key: 'stock', icon: '📈', label: '股票', css: 'asset-stock', sub: '持仓市值' },
  { key: 'bond', icon: '📜', label: '债券', css: 'asset-bond', sub: '债权' },
  { key: 'precious_metal', icon: '🪙', label: '贵金属', css: 'asset-precious-metal', sub: '黄金/白银等' },
  { key: 'liability', icon: '🏠', label: '负债', css: 'asset-liability', sub: '总负债' },
]

const familyAssetCardConfigs = [
  { key: 'cash', label: '现金' },
  { key: 'deposit', label: '定期' },
  { key: 'fund', label: '基金' },
  { key: 'stock', label: '股票' },
  { key: 'bond', label: '债券' },
  { key: 'precious_metal', label: '贵金属' },
  { key: 'liability', label: '负债' },
]

// 个人模式：资产key -> summary 中的值（liability 特殊映射到 total_liability）
function cardAssetValue(key) {
  if (key === 'liability') return summary.total_liability
  return summary[key] || 0
}

// 家庭模式：资产key -> 成员 summary 中的值
function familyCardValue(m, key) {
  if (key === 'liability') return m.summary.total_liability
  return m.summary[key] || 0
}

function adjustedMember(memberId, m) {
  const s = { ...m.summary }
  let hiddenAssetTotal = 0
  for (const cat of CAT_KEYS) {
    if (isFamilyHidden(memberId, cat)) {
      hiddenAssetTotal += (s[cat] || 0)
    }
  }
  s.total_asset = (s.total_asset || 0) - hiddenAssetTotal
  if (isFamilyHidden(memberId, 'liability')) {
    s.total_liability = 0
  }
  s.net_worth = s.total_asset - (s.total_liability || 0)
  return s
}

const adjustedFamilyTotal = computed(() => {
  if (!familyData.members) return { total_asset: 0, total_liability: 0, net_worth: 0 }
  let ta = 0, tl = 0
  for (const [mid, m] of Object.entries(familyData.members)) {
    const adj = adjustedMember(mid, m)
    ta += adj.total_asset
    tl += adj.total_liability
  }
  return { total_asset: ta, total_liability: tl, net_worth: ta - tl }
})

// 家庭隐藏 FAB
const showFamilyHidden = ref(false)
const familyHiddenCount = computed(() => {
  let count = 0
  for (const arr of Object.values(familyHiddenAssets.value || {})) {
    count += arr.length
  }
  return count
})
const familyHiddenList = computed(() => {
  const result = []
  if (!familyData.members) return result
  for (const [mid, m] of Object.entries(familyData.members)) {
    const cats = getFamilyHidden(mid)
    if (cats.length > 0) {
      result.push({
        mid,
        uid: mid,
        name: m.display_name || m.username,
        cats: cats.map(c => ({ key: c, label: CAT_LABEL_MAP[c] || c })),
      })
    }
  }
  return result
})

const hasAnyAsset = computed(() => {
  return summary.cash > 0 || summary.deposit > 0 || summary.fund > 0 || 
         summary.stock > 0 || summary.bond > 0 || summary.precious_metal > 0 || 
         summary.total_liability > 0
})

async function loadAll() {
  try {
    const { data } = await getSummary(scope.value)
    if (scope.value === 'family') {
      familyData.members = data.members || null
      familyData.family = data.family || null
      // Load family investment summary
      try {
        const invRes = await getFamilyInvestmentSummary()
        Object.assign(familyInvestSummary, invRes.data || { total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
      } catch (e) {
        console.error('家庭投资汇总加载失败:', e)
        Object.assign(familyInvestSummary, { total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
      }
    } else {
      Object.assign(summary, data)
      // Load investment summary
      try {
        const invRes = await getInvestmentSummary()
        Object.assign(investSummary, invRes.data || { total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
      } catch {
        Object.assign(investSummary, { total_cost: 0, total_market_value: 0, total_profit: 0, total_profit_pct: 0 })
      }
      // Load deposit interest if any deposit
      if (summary.deposit > 0) {
        try {
          const { data: detail } = await getDetail('deposit')
          const deposits = detail?.deposit || []
          let totalInterest = 0
          for (const d of deposits) {
            const { data: interest } = await getDepositInterest(d.id)
            totalInterest += interest.accrued_interest || 0
          }
          depositInterest.value = totalInterest
        } catch (e) {
          console.error('存款利息加载失败:', e)
        }
      }
    }
  } catch {}
}

async function loadTrend() {
  try {
    const { data } = await getTrend(30)
    trendData.value = data || []
  } catch {
    trendData.value = []
    console.error('加载趋势数据失败')
  }
}

// ── 趋势数据排除隐藏类别（个人模式）──
const displayTrendData = computed(() => {
  let data = trendData.value
  if (hiddenAssets.value.length > 0) {
    data = data.map(d => {
      const excluded = hiddenAssets.value.reduce((sum, cat) => sum + (d[cat] || 0), 0)
      return { ...d, net_worth: (d.net_worth || 0) - excluded }
    })
  }
  return data
})

async function loadFamilyTrend() {
  try {
    const { data } = await getFamilyTrend(30)
    familyTrendData.value = data || {}
  } catch {
    familyTrendData.value = {}
    console.error('加载家庭趋势数据失败')
  }
}

function formatInterest(amount) {
  const v = Number(amount) || 0
  if (v >= 10000) return (v/10000).toFixed(1) + '万'
  if (v >= 1000) return (v/1000).toFixed(1) + 'k'
  return v.toFixed(0)
}

onMounted(() => { loadAll(); loadTrend() })
watch(scope, () => { loadAll(); if (scope.value === 'family') { loadFamilyTrend() } })
// 家庭隐藏资产变化时重新加载趋势（趋势数据无分类明细，需重取）
// ⚠️ 延迟 600ms 确保 saveRemote(PUT /user/settings) 先于 loadFamilyTrend(GET /family/trend) 完成，
// 避免后端读到旧的 familyHiddenAssets 导致趋势排除错误类别
let _familyTrendDelay = null
watch(familyHiddenAssets, () => {
  if (scope.value !== 'family') return
  clearTimeout(_familyTrendDelay)
  _familyTrendDelay = setTimeout(() => loadFamilyTrend(), 600)
}, { deep: true })
</script>

<style scoped>
.trend-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 0 20px 12px 20px;
}
.date-range {
  display: flex;
  align-items: center;
  gap: 6px;
}
.top-fixed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.glass-card {
  background: rgba(255, 251, 254, 0.72);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 0.5px solid rgba(103, 80, 164, 0.08);
  box-shadow: var(--md-elevation-3);
}
.glass-card .card-icon {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 28px;
  opacity: 0.2;
  transition: opacity 0.3s;
}
.glass-card:hover .card-icon {
  opacity: 0.4;
}

.dynamic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}
.asset-card {
  position: relative;
  overflow: hidden;
  border-left: 4px solid;
  transition: transform 0.2s var(--ease-spring), box-shadow 0.2s;
}
.asset-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card-hover);
}

/* top row: label + eye */
.asset-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.eye-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px;
  border-radius: var(--radius-full);
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s var(--ease-apple);
  color: var(--c-text-tertiary);
}
.asset-card:hover .eye-btn { opacity: 0.5; }
.eye-btn:hover { opacity: 1 !important; color: var(--c-text); background: rgba(0,0,0,0.04); }
.eye-btn svg { width: 15px; height: 15px; }

.asset-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 14px;
  color: var(--c-text-secondary);
}
.asset-icon {
  font-size: 20px;
}
.asset-value {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}
.asset-sub {
  font-size: 12px;
  color: var(--c-text-tertiary);
}

/* Asset-specific colors */
.asset-cash { border-left-color: #10B981; background: linear-gradient(135deg, rgba(16,185,129,0.05) 0%, rgba(16,185,129,0.02) 100%); }
.asset-cash .asset-value { color: #10B981; }
.asset-deposit { border-left-color: #F59E0B; background: linear-gradient(135deg, rgba(245,158,11,0.05) 0%, rgba(245,158,11,0.02) 100%); }
.asset-deposit .asset-value { color: #F59E0B; }
.asset-fund { border-left-color: #6366F1; background: linear-gradient(135deg, rgba(99,102,241,0.05) 0%, rgba(99,102,241,0.02) 100%); }
.asset-fund .asset-value { color: #6366F1; }
.asset-stock { border-left-color: #EF4444; background: linear-gradient(135deg, rgba(239,68,68,0.05) 0%, rgba(239,68,68,0.02) 100%); }
.asset-stock .asset-value { color: #EF4444; }
.asset-bond { border-left-color: #8B5CF6; background: linear-gradient(135deg, rgba(139,92,246,0.05) 0%, rgba(139,92,246,0.02) 100%); }
.asset-bond .asset-value { color: #8B5CF6; }
.asset-precious-metal { border-left-color: #F59E0B; background: linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(218,165,32,0.03) 100%); }
.asset-precious-metal .asset-value { color: #DAA520; }
.asset-liability { border-left-color: #F97316; background: linear-gradient(135deg, rgba(249,115,22,0.05) 0%, rgba(249,115,22,0.02) 100%); }
.asset-liability .asset-value { color: #F97316; }

.empty-assets {
  text-align: center;
  padding: 60px 20px;
  background: var(--md-surface-container-low);
  border-radius: var(--radius-xl);
  margin-bottom: 24px;
  border: 1px dashed var(--md-outline-variant);
}
.empty-assets .empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.3;
}
.empty-assets h4 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--c-text);
}
/* Floating hidden assets button */
.hidden-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
}
.hidden-fab-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--md-surface-container-highest);
  color: var(--c-text);
  border: none;
  box-shadow: var(--md-elevation-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.2s var(--ease-emphasized);
}
.hidden-fab-btn:hover {
  background: var(--md-surface-container-high);
  box-shadow: var(--md-elevation-4);
  transform: scale(1.05);
}
.hidden-fab-btn svg {
  width: 24px;
  height: 24px;
}
.hidden-fab-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--md-error);
  color: var(--md-on-error);
  font-size: 11px;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}
.hidden-popover {
  position: absolute;
  bottom: 64px;
  right: 0;
  width: 240px;
  background: var(--md-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--md-elevation-4);
  border: 1px solid var(--md-outline-variant);
  overflow: hidden;
}
.hidden-popover-title {
  padding: 16px;
  font-weight: 600;
  font-size: 14px;
  color: var(--c-text-secondary);
  border-bottom: 1px solid var(--md-outline-variant);
}
.hidden-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--md-outline-variant);
}
.hidden-item:last-child {
  border-bottom: none;
}
.hidden-item-label {
  font-size: 14px;
  color: var(--c-text);
}
.restore-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-full);
  background: var(--md-surface-container-highest);
  color: var(--c-text);
  font-size: 13px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
.restore-btn:hover {
  background: var(--md-surface-container-high);
  color: var(--md-primary);
}
.restore-btn svg {
  width: 14px; height: 14px;
}

/* Mobile: hidden-fab above bottom nav */
@media (max-width: 600px) {
  .hidden-fab {
    bottom: 80px;
    right: 16px;
  }
  .hidden-fab-btn {
    width: 48px;
    height: 48px;
  }
  .hidden-popover {
    bottom: 56px;
    right: 0;
    width: 220px;
  }
}

.invest-summary-card {
  margin-top: var(--space-4);
  margin-bottom: var(--space-4);
  padding: 20px;
  background: var(--md-surface-container-low);
  border-radius: var(--radius-xl);
  border: 1px solid var(--md-outline-variant);
}

.invest-summary-header {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-secondary);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--md-outline-variant);
}

.invest-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

.invest-summary-item {
  text-align: center;
}

.invest-summary-label {
  font-size: 12px;
  color: var(--c-text-tertiary);
  margin-bottom: 4px;
}

.invest-summary-value {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.3px;
  color: var(--c-text);
}

.invest-summary-item.profit .invest-summary-value {
  color: #10b981;
}

.invest-summary-item.loss .invest-summary-value {
  color: #ef4444;
}

/* ── Family mode category cards ── */
.family-cat-card {
  position: relative;
}
.family-cat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.family-cat-card .eye-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px;
  border-radius: var(--radius-full);
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s var(--ease-apple);
  color: var(--md-on-surface-variant);
}
.family-cat-card:hover .eye-btn {
  opacity: 0.5;
}
.family-cat-card .eye-btn:hover {
  opacity: 1 !important;
  color: var(--md-on-surface);
  background: rgba(0,0,0,0.04);
}
.family-cat-card .eye-btn svg {
  width: 15px; height: 15px;
}
.family-cat-card.family-hidden {
  opacity: 0.45;
  filter: grayscale(0.3);
}
.family-cat-card.family-hidden:hover {
  opacity: 0.7;
  filter: grayscale(0.1);
}
.family-cat-card .family-cat-top .label {
  margin-bottom: 0;
}

@media (max-width: 600px) {
  .glass-card .value {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.5px;
  }
}
</style>
